'use strict';
const cards = document.getElementById('cards');
const count = document.getElementById('count');
const status = document.getElementById('status');
const search = document.getElementById('search');
const filterButtons = Array.from(document.querySelectorAll('[data-filter]'));
const detailsDialog = document.getElementById('detailsDialog');
const detailsTitle = document.getElementById('detailsTitle');
const detailsContent = document.getElementById('detailsContent');
const platformNames = {android:'اندروید', windows:'ویندوز',web:'وب'};
let data = [];
let platformFilter = 'all';
let offlineMode = false;

function el(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (value !== undefined) element.textContent = value;
  return element;
}
function validUrl(value) {
  try { const url = new URL(value); return url.protocol === 'https:'; }
  catch { return false; }
}
function showDetails(app) {
  detailsTitle.textContent = app.name_fa;
  detailsContent.replaceChildren();
  function fact(label, value) {
    const section = el('div', 'details-fact');
    section.append(el('strong', '', label), el('p', '', String(value)));
    detailsContent.append(section);
  }
  fact('نام لاتین', app.name_en);
  fact('معرفی', app.description);
  fact('پلتفرم', app.platforms.map(p => platformNames[p] || p).join('، '));
  if (app.status !== 'released') {
    fact('وضعیت', 'در حال توسعه؛ هنوز نسخه یا فایل قابل دریافت وجود ندارد.');
  } else {
    fact('نسخهٔ ثبت‌شده', app.version);
    if (app.changelog) fact('تغییرات نسخه', app.changelog);
    if (app.release_proof && typeof app.release_proof === 'object') {
      if (app.release_proof.source_repo) fact('مخزن منبع ثبت‌شده', app.release_proof.source_repo);
      if (app.release_proof.source_sha) fact('شناسهٔ تغییر منبع', app.release_proof.source_sha);
      const digest = app.release_proof.sha256 || app.release_proof.artifact_sha256;
      if (digest) fact('SHA-256 ثبت‌شدهٔ بسته', digest);
    }
    fact('محدودیت بررسی', 'این مشخصات از کاتالوگ انتشار خوانده می‌شوند و به‌تنهایی اثبات امضای واقعی فایل یا سلامت لحظه‌ای مقصد نیستند.');
  }
  detailsDialog.showModal();
}
document.getElementById('detailsClose').addEventListener('click', () => detailsDialog.close());

function render() {
  const term = search.value.trim().toLocaleLowerCase('fa');
  const matched = data.filter(app => {
    const searchable = `${app.name_fa} ${app.name_en} ${app.description}`.toLocaleLowerCase('fa');
    return searchable.includes(term) && (platformFilter === 'all' || app.platforms.includes(platformFilter));
  });
  cards.replaceChildren();
  count.textContent = `${matched.length} برنامه`;
  status.textContent = matched.length
    ? (offlineMode ? 'حالت آفلاین: فقط فهرست برنامه‌های در حال توسعه نمایش داده می‌شود؛ هیچ لینکی برای نصب فعال نیست.' : '')
    : 'برنامه‌ای با این مشخصات پیدا نشد.';
  matched.forEach(app => {
    const card = el('article', 'card');
    const top = el('div', 'card-top');
    const icon = el('div', 'app-icon', app.symbol || 'ه‍');
    icon.setAttribute('aria-hidden','true');
    icon.style.setProperty('--icon-bg', /^#[0-9a-fA-F]{6}$/.test(app.color || '') ? app.color : '#253f50');
    const heading = el('div');
    heading.append(el('h3', '', app.name_fa), el('p', '', app.name_en));
    top.append(icon, heading);
    const desc = el('p', 'app-description', app.description);
    const footer = el('div', 'card-footer');
    const meta = el('div');
    app.platforms.forEach(p => meta.append(el('span', 'pill', platformNames[p] || p)));
    meta.append(el('span', `badge ${app.status === 'released' ? 'live' : ''}`, app.status === 'released' ? `نسخهٔ ${app.version}` : 'در حال توسعه'));
    footer.append(meta);
    const detailButton = el('button', 'detail-button', 'جزئیات');
    detailButton.type = 'button';
    detailButton.setAttribute('aria-label', `مشاهدهٔ جزئیات ${app.name_fa}`);
    detailButton.addEventListener('click', () => showDetails(app));
    footer.append(detailButton);
    if (app.status === 'released' && validUrl(app.download_url)) {
      const isWeb = app.platforms.length === 1 && app.platforms[0] === 'web';
      const link = el('a', 'download', isWeb ? 'باز کردن برنامه' : 'دریافت');
      link.href = app.download_url;
      link.rel = 'noopener noreferrer';
      link.target = '_blank';
      link.setAttribute('aria-label', `${isWeb ? 'باز کردن' : 'دریافت'} ${app.name_fa}`);
      footer.append(link);
    } else footer.append(el('span', 'disabled', 'هنوز منتشر نشده'));
    card.append(top, desc, footer);
    cards.append(card);
  });
}
async function load() {
  status.textContent = 'در حال بارگذاری کاتالوگ...';
  try {
    const response = await fetch('./catalog/apps.json', {cache:'no-store'});
    if (!response.ok) throw new Error(String(response.status));
    const payload = await response.json();
    if (!Array.isArray(payload.apps)) throw new Error('invalid catalog');
    data = payload.apps;
    offlineMode = false;
    render();
  } catch (err) {
    console.warn('Live catalogue unavailable; attempting safe offline planned-only snapshot', err);
    try {
      const cached = await fetch('./catalog/planned-offline.json', {cache:'force-cache'});
      if (!cached.ok) throw new Error(String(cached.status));
      const snapshot = await cached.json();
      if (!Array.isArray(snapshot.apps) || !snapshot.apps.every(app =>
        app.status === 'planned' && app.download_url === null && app.version === null)) {
        throw new Error('invalid offline snapshot');
      }
      data = snapshot.apps;
      offlineMode = true;
      render();
    } catch (offlineError) {
      status.textContent = 'فهرست برنامه‌ها در دسترس نیست. پس از برقراری اتصال، صفحه را تازه کنید.';
      console.error('Safe offline snapshot unavailable', offlineError);
    }
  }
}
filterButtons.forEach(button => button.addEventListener('click', () => {
  platformFilter = button.dataset.filter;
  filterButtons.forEach(b => { const on = b === button; b.classList.toggle('active',on); b.setAttribute('aria-pressed',String(on)); });
  render();
}));
search.addEventListener('input',render);
document.getElementById('year').textContent=String(new Date().getFullYear());
const themeButton = document.getElementById('toggleTheme');
try {if(localStorage.getItem('hamapp-theme')==='light')document.documentElement.classList.add('light')} catch {}
themeButton.addEventListener('click',() => {const light=document.documentElement.classList.toggle('light');try {localStorage.setItem('hamapp-theme',light?'light':'dark')} catch {}});
let deferredInstall;
window.addEventListener('beforeinstallprompt', e => {e.preventDefault();deferredInstall=e;document.getElementById('installPwa').classList.remove('hidden')});
document.getElementById('installPwa').addEventListener('click',async() => {if(!deferredInstall)return;deferredInstall.prompt();await deferredInstall.userChoice;deferredInstall=null;document.getElementById('installPwa').classList.add('hidden')});
if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost')) {
  window.addEventListener('load',() => navigator.serviceWorker.register('./sw.js').catch(console.warn));
}
load();
