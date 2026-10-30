// Live Duplicate Detection & Real-time Client interactions
document.addEventListener('DOMContentLoaded', () => {
    const titleInput = document.getElementById('title');
    const descInput = document.getElementById('description');
    const catSelect = document.getElementById('category');
    const duplicateBox = document.getElementById('duplicate-warning-box');
    const duplicateList = document.getElementById('duplicate-items-list');

    let debounceTimer;

    function checkDuplicates() {
        if (!titleInput || !duplicateBox) return;

        const title = titleInput.value.trim();
        const description = descInput ? descInput.value.trim() : '';
        const category = catSelect ? catSelect.value : '';

        if (title.length < 5) {
            duplicateBox.style.display = 'none';
            return;
        }

        fetch('/api/check-duplicates', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title, description, category })
        })
        .then(res => res.json())
        .then(data => {
            if (data.duplicates && data.duplicates.length > 0) {
                duplicateBox.style.display = 'block';
                duplicateList.innerHTML = '';
                data.duplicates.forEach(item => {
                    const li = document.createElement('li');
                    li.className = 'py-1';
                    li.innerHTML = `<strong>#${item.complaint_id}</strong> - ${item.title} <span class="badge badge-light">${item.status}</span> <span class="text-muted">(${item.similarity}% match)</span>`;
                    duplicateList.appendChild(li);
                });
            } else {
                duplicateBox.style.display = 'none';
            }
        })
        .catch(err => console.error("Duplicate check error:", err));
    }

    if (titleInput) {
        titleInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(checkDuplicates, 500);
        });
    }

    // Star rating picker
    const starContainer = document.getElementById('star-rating');
    const ratingInput = document.getElementById('rating-value');
    if (starContainer && ratingInput) {
        const stars = starContainer.querySelectorAll('.star');
        stars.forEach(star => {
            star.addEventListener('click', () => {
                const val = parseInt(star.getAttribute('data-value'), 10);
                ratingInput.value = val;
                stars.forEach(s => {
                    const sVal = parseInt(s.getAttribute('data-value'), 10);
                    if (sVal <= val) {
                        s.classList.add('selected');
                        s.innerHTML = '★';
                    } else {
                        s.classList.remove('selected');
                        s.innerHTML = '☆';
                    }
                });
            });
        });
    }
});

