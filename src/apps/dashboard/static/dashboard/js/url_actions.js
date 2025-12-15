document.addEventListener('DOMContentLoaded', () => {
  const isValidUrl = string => {
    try {
      const url = new URL(string);
      return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (_) {
      return false;
    }
  };

  const getCookie = name => {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      document.cookie.split(';').forEach(cookie => {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        }
      });
    }
    return cookieValue;
  };

  const table = document.querySelector('table');
  if (!table) return;

  const csrftoken = getCookie('csrftoken');

  const enableEdit = (id)=> {
    const input = document.getElementById('original-' + id);
    input.removeAttribute('readonly');
    input.classList.add('border', 'border-blue-400', 'bg-white');
    input.focus();
    toggleButtons(id, { edit: false, save: true });
  };

  const cancelEdit = id => {
    const input = document.getElementById('original-' + id);
    input.setAttribute('readonly', true);
    input.classList.remove('border', 'border-blue-400', 'bg-white');
    toggleButtons(id, { edit: true, save: false });
  };

  const toggleButtons = (id, { edit, save }) => {
    const row = document.getElementById('link-row-' + id);
    const editBtn = row.querySelector(`.action-edit[data-link-id="${id}"]`);
    const saveBtn = row.querySelector(`.action-save[data-link-id="${id}"]`);
    if (editBtn) editBtn.classList.toggle('hidden', !edit);
    if (saveBtn) saveBtn.classList.toggle('hidden', !save);
  };

  const saveEdit = async id => {
    const row = document.getElementById('link-row-' + id);
    const input = document.getElementById('original-' + id);
    const newValue = input.value.trim();

    if (!newValue) return alert('A URL não pode ficar vazia.');
    if (!isValidUrl(newValue)) return alert('URL inválida. Certifique-se de incluir http:// ou https://');

    const updateUrl = row.querySelector('.ajax-url-update').value;

    try {
      const resp = await fetch(updateUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
        body: JSON.stringify({ original_url: newValue })
      });

      if (!resp.ok) throw resp;

      const data = await resp.json();
      if (data.success) {
        cancelEdit(id);
        input.classList.add('bg-green-50');
        setTimeout(() => input.classList.remove('bg-green-50'), 1200);
      } else {
        alert(data.error || 'Erro ao salvar');
      }
    } catch (err) {
      console.error(err);
      alert('Erro na requisição. Veja o console.');
    }
  };

  const deleteLink = async id => {
    if (!confirm('Tem certeza que deseja excluir este link?')) return;

    const row = document.getElementById('link-row-' + id);
    const deleteUrl = row.querySelector('.ajax-url-delete').value;

    try {
      const resp = await fetch(deleteUrl, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrftoken }
      });

      if (!resp.ok) throw resp;

      const data = await resp.json();
      if (data.success) {
        row.remove();
      } else {
        alert(data.error || 'Erro ao excluir link');
      }
    } catch (err) {
      console.error(err);
      alert('Erro na requisição. Veja o console.');
    }
  };

  window.cancelEdit = cancelEdit;

  // Event delegation
  table.addEventListener('click', e => {
    let btn = e.target;
    while (btn && !btn.classList.contains('action-btn')) btn = btn.parentElement;
    if (!btn) return;

    const linkId = btn.dataset.linkId;
    if (btn.classList.contains('action-edit')) enableEdit(linkId);
    else if (btn.classList.contains('action-save')) saveEdit(linkId);
    else if (btn.classList.contains('action-delete')) deleteLink(linkId);
  });
});
