function toggleMenu() {
  const menu = document.getElementById("sideMenu");
  const overlay = document.querySelector(".menu-overlay");
  if (menu) menu.classList.toggle("open");
  if (overlay) overlay.classList.toggle("open");
  closeBotsMenu();
}

const botsDropdown = document.getElementById("botsDropdown");
const botsToggle   = document.getElementById("botsToggle");
const botsSubmenu  = document.getElementById("botsSubmenu");
let closeTimer = null;

function openBotsMenu() {
  if (!botsToggle || !botsSubmenu) return;
  clearTimeout(closeTimer);
  const rect = botsToggle.getBoundingClientRect();
  botsSubmenu.style.top = rect.top + "px";
  botsSubmenu.classList.add("open");
}

function scheduleClose() {
  closeTimer = setTimeout(closeBotsMenu, 80);
}

function closeBotsMenu() {
  if (botsSubmenu) botsSubmenu.classList.remove("open");
}

if (botsDropdown) {
  botsDropdown.addEventListener("mouseenter", openBotsMenu);
  botsDropdown.addEventListener("mouseleave", scheduleClose);
}
if (botsSubmenu) {
  botsSubmenu.addEventListener("mouseenter", () => clearTimeout(closeTimer));
  botsSubmenu.addEventListener("mouseleave", scheduleClose);
}



fetch("/api/me", { credentials: "same-origin" })
  .then(function (r) { return r.json(); })
  .then(function (data) {
    const loginLink = document.querySelector('.side-menu a[href="/login"]');
    if (!loginLink) return;

    if (data.logged_in) {
      const userBlock = document.createElement("div");
      userBlock.className = "side-menu-user";
      userBlock.innerHTML =
        '<span class="side-menu-username">' + data.username + '</span>' +
        '<a href="/api/logout" class="side-menu-logout">Logout</a>';
      loginLink.replaceWith(userBlock);
    }
  })
  .catch(function () {});
