import io
import csv
from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from app.models import db, Complaint, User, Department, Feedback

def utc_now():
    return datetime.now(timezone.utc)

def generate_csv_report(complaints) -> io.StringIO:
    """Generates a CSV report buffer from a complaint query or list."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        'Complaint ID', 'Title', 'Category', 'Priority', 'Status',
        'Submitted By', 'Submitter Email', 'Department', 'Assigned To',
        'Submitted Date', 'Last Updated', 'Resolution Note', 'Rating'
    ])

    for c in complaints:
        writer.writerow([
            c.complaint_id,
            c.title,
            c.category,
            c.priority,
            c.status,
            c.submitter.full_name if c.submitter else 'N/A',
            c.submitter.email if c.submitter else 'N/A',
            c.department.name if c.department else 'Unassigned',
            c.assignee.full_name if c.assignee else 'Unassigned',
            c.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            c.updated_at.strftime('%Y-%m-%d %H:%M:%S') if c.updated_at else 'N/A',
            c.resolution_note or 'N/A',
            c.feedback.rating if c.feedback else 'None'
        ])

    output.seek(0)
    return output

def generate_pdf_report(complaints) -> io.BytesIO:
    """Generates a formatted PDF summary report using ReportLab."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=30,
        rightMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    elements = []
    styles = getSampleStyleSheet()

    # Title & Header
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'ReportSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=15
    )

    elements.append(Paragraph("SmartComplaint System — Complaint Report", title_style))
    elements.append(Paragraph(f"Generated on {utc_now().strftime('%B %d, %Y at %H:%M UTC')} | Total Records: {len(complaints)}", subtitle_style))
    elements.append(Spacer(1, 10))

    # Table Data
    table_data = [[
        'Complaint ID', 'Title', 'Category', 'Priority', 'Status', 'Department', 'Date'
    ]]

    cell_style = ParagraphStyle('CellText', parent=styles['Normal'], fontSize=8, leading=10)
    header_style = ParagraphStyle('HeaderCell', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)

    # Format header
    table_data[0] = [Paragraph(col, header_style) for col in table_data[0]]

    for c in complaints:
        table_data.append([
            Paragraph(c.complaint_id, cell_style),
            Paragraph(c.title[:40] + ('...' if len(c.title) > 40 else ''), cell_style),
            Paragraph(c.category or 'General', cell_style),
            Paragraph(c.priority, cell_style),
            Paragraph(c.status, cell_style),
            Paragraph(c.department.name if c.department else 'Unassigned', cell_style),
            Paragraph(c.created_at.strftime('%Y-%m-%d'), cell_style)
        ])

    table = Table(table_data, colWidths=[90, 220, 90, 65, 80, 110, 75])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

def get_analytics_summary():
    """Calculates overall metrics, status breakdowns, priority distribution, and resolution stats."""
    total_complaints = Complaint.query.count()
    status_counts = dict(db.session.query(Complaint.status, func.count(Complaint.id)).group_by(Complaint.status).all())

    pending = status_counts.get('Submitted', 0) + status_counts.get('Under Review', 0)
    in_progress = status_counts.get('Assigned', 0) + status_counts.get('In Progress', 0)
    resolved = status_counts.get('Resolved', 0)
    rejected = status_counts.get('Rejected', 0)

    # Resolution rate
    resolution_rate = round((resolved / total_complaints * 100), 1) if total_complaints > 0 else 0

    # Priority distribution
    priority_counts = dict(db.session.query(Complaint.priority, func.count(Complaint.id)).group_by(Complaint.priority).all())

    # Category distribution
    category_counts = dict(db.session.query(Complaint.category, func.count(Complaint.id)).group_by(Complaint.category).all())

    # Average Feedback Rating
    avg_rating_result = db.session.query(func.avg(Feedback.rating)).scalar()
    avg_rating = round(float(avg_rating_result), 1) if avg_rating_result else 0.0

    # Monthly Trends (last 6 months)
    today = utc_now()
    monthly_labels = []
    monthly_counts = []
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=i * 30)
        month_label = month_date.strftime('%b %Y')
        monthly_labels.append(month_label)
        
        start_date = datetime(month_date.year, month_date.month, 1)
        if month_date.month == 12:
            end_date = datetime(month_date.year + 1, 1, 1)
        else:
            end_date = datetime(month_date.year, month_date.month + 1, 1)
            
        c_count = Complaint.query.filter(Complaint.created_at >= start_date, Complaint.created_at < end_date).count()
        monthly_counts.append(c_count)

    return {
        'total': total_complaints,
        'pending': pending,
        'in_progress': in_progress,
        'resolved': resolved,
        'rejected': rejected,
        'resolution_rate': resolution_rate,
        'avg_rating': avg_rating,
        'status_counts': status_counts,
        'priority_counts': priority_counts,
        'category_counts': category_counts,
        'monthly_labels': monthly_labels,
        'monthly_counts': monthly_counts
    }
