// Modal con tabs y render de listas de interferencias
export function initModal(){
  const modalEl = document.getElementById('modal');
  const closeBtn = document.getElementById('modalClose');
  if (closeBtn) closeBtn.onclick = ()=> modalEl.style.display='none';

  const tabBtns = [...document.querySelectorAll('[data-tab]')];
  tabBtns.forEach(btn=>{
    btn.onclick = ()=>{
      const tab = btn.dataset.tab;
      document.getElementById('tab_carriers').style.display = tab==='carriers'?'block':'none';
      document.getElementById('tab_im2').style.display = tab==='im2'?'block':'none';
      document.getElementById('tab_im3').style.display = tab==='im3'?'block':'none';
    };
  });
}

// modal.js
export function showInterferenceModal(result, title='Interferencias'){
  const items = Array.isArray(result?.items) ? result.items : [];
  document.getElementById('modalTitle').textContent = title;

  const carr = items.filter(x => x?.kind === 'carrier');
  const im2  = items.filter(x => x?.kind === 'im2');
  const im3  = items.filter(x => x?.kind === 'im3');

  const fx = (v, n=1) => Number.isFinite(v) ? v.toFixed(n) : '';

  const renderList = (arr=[])=> `<table style="width:100%; border-collapse:collapse;">
    <thead><tr><th align="left">Tipo</th><th align="right">f (MHz)</th><th align="right">Raw (dBm)</th><th align="right">Filtro (dBm)</th><th align="left">IDs</th></tr></thead>
    <tbody>
      ${arr.slice(0,60).map(it=>`
        <tr>
          <td>${it?.kind ?? ''}</td>
          <td align="right">${fx(it?.f_MHz, 4)}</td>
          <td align="right">${fx(it?.raw_level_dBm, 1)}</td>
          <td align="right">${fx(it?.after_filter_dBm, 1)}</td>
          <td>${(it?.contributor_ids || []).join(', ')}</td>
        </tr>`).join('')}
    </tbody></table>`;

  document.getElementById('tab_carriers').innerHTML = renderList(carr);
  document.getElementById('tab_im2').innerHTML = renderList(im2);
  document.getElementById('tab_im3').innerHTML = renderList(im3);

  const modalEl = document.getElementById('modal');
  modalEl.style.display = 'flex';
  const defaultBtn = document.querySelector('[data-tab="carriers"]');
  if (defaultBtn) defaultBtn.click();
}
