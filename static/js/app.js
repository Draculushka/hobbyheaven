/* HobbyHeaven — shared utilities */

function previewImage(input, previewId) {
    var preview = document.getElementById(previewId);
    var container = document.getElementById(previewId + 'Container');
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function (e) {
            preview.src = e.target.result;
            container.classList.remove('hidden');
        };
        reader.readAsDataURL(input.files[0]);
    }
}

function openImage(src) {
    var modal = document.getElementById('imageModal');
    var img = document.getElementById('modalImg');
    img.src = src;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    modal.focus();
}

function closeImageModal() {
    var modal = document.getElementById('imageModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

function toggleSidebar() {
    var content = document.getElementById('sidebar-content');
    var btn = document.getElementById('toggle-sidebar');
    if (content && btn) {
        content.classList.toggle('hidden');
        btn.setAttribute('aria-expanded', content.classList.contains('hidden') ? 'false' : 'true');
    }
}

document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        closeImageModal();
    }
});
