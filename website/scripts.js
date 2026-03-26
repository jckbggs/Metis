function toggleMenu() {
  const menu = document.getElementById('sideMenu');
  const overlay = document.querySelector('.menu-overlay');
  menu.classList.toggle('open');
  overlay.classList.toggle('open');
  closeBotsMenu();
}

const botsDropdown = document.getElementById('botsDropdown');
const botsToggle   = document.getElementById('botsToggle');
const botsSubmenu  = document.getElementById('botsSubmenu');
let closeTimer = null;

function openBotsMenu() {
  clearTimeout(closeTimer);
  const rect = botsToggle.getBoundingClientRect();
  botsSubmenu.style.top = rect.top + 'px';
  botsSubmenu.classList.add('open');
}

function scheduleClose() {
  closeTimer = setTimeout(closeBotsMenu, 80);
}

function closeBotsMenu() {
  botsSubmenu.classList.remove('open');
}

botsDropdown.addEventListener('mouseenter', openBotsMenu);
botsDropdown.addEventListener('mouseleave', scheduleClose);
botsSubmenu.addEventListener('mouseenter', () => clearTimeout(closeTimer));
botsSubmenu.addEventListener('mouseleave', scheduleClose);