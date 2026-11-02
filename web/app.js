'use strict';
const cards = document.getElementById('cards');
const count = document.getElementById('count');
const status = document.getElementById('status');
const search = document.getElementById('search');
const filterButtons = Array.from(document.querySelectorAll('[data-filter]'));
const platformNames = {android:'اندروید', windows:'ویندوز',web:'وب'};
let data = [];
let platformFilter = 'all';

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
function render() {
  const term = search.value.trim().toLocaleLowerCase('fa');
  const matched = data.filter(app => {
    const searchable = `${app.name_fa} ${app.name_en} ${app.description}`.toLocaleLowerCase('fa');
    return searchable.includes(term) && (platformFilter === 'all' || app.platforms.includes(platformFilter));
  });
  cards.replaceChildren();
  count.textContent = `${matched.length} برنامه`;
  status.textContent = matched.length ? '' : 'برنامه‌ای با این مشخصات پیدا نشد.';
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
    render();
  } catch (err) {
    status.textContent = 'بارگذاری برنامه‌ها ممکن نشد. اتصال اینترنت را بررسی و صفحه را تازه کنید.';
    console.error('Catalog loading error', err);
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
