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

const errors = {
      missing_fields: "Please fill in all required fields.",
      username_too_long: "Username must be 50 characters or fewer.",
      password_mismatch: "Passwords do not match.",
      password_too_short: "Password must be at least 6 characters.",
      username_taken: "That username is already taken. Please choose another.",
      db_error: "A database error occurred. Please try again.",
    };

const params = new URLSearchParams(window.location.search);
const err = params.get("error");
  if (err) {
    const box = document.getElementById("errorBox");
    box.textContent = errors[err] || "An error occurred. Please try again.";
    box.classList.add("visible");
    }

document.getElementById("signupForm").addEventListener("submit", function (e) {
  const pw = document.getElementById("password").value;
  const cpw = document.getElementById("confirm_password").value;
    if (pw !== cpw) {
      e.preventDefault();
      const box = document.getElementById("errorBox");
      box.textContent = errors.password_mismatch;
      box.classList.add("visible");
      }
    });


