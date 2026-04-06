/**
 * Main
 */

"use strict";

let menu, animate;
const MENU_NAV_DELAY_MS = 350;

(function () {
  // Initialize menu
  //-----------------

  let layoutMenuEl = document.querySelectorAll("#layout-menu");
  layoutMenuEl.forEach(function (element) {
    menu = new Menu(element, {
      orientation: "vertical",
      closeChildren: false,
    });
    // Change parameter to true if you want scroll animation
    window.Helpers.scrollToActive((animate = false));
    window.Helpers.mainMenu = menu;
  });

  // Initialize menu togglers and bind click on each
  let menuToggler = document.querySelectorAll(".layout-menu-toggle");
  menuToggler.forEach((item) => {
    item.addEventListener("click", (event) => {
      event.preventDefault();
      window.Helpers.toggleCollapsed();
    });
  });

  // Display menu toggle (layout-menu-toggle) on hover with delay
  let delay = function (elem, callback) {
    let timeout = null;
    elem.onmouseenter = function () {
      // Set timeout to be a timer which will invoke callback after 300ms (not for small screen)
      if (!Helpers.isSmallScreen()) {
        timeout = setTimeout(callback, 300);
      } else {
        timeout = setTimeout(callback, 0);
      }
    };

    elem.onmouseleave = function () {
      // Clear any timers set to timeout
      document.querySelector(".layout-menu-toggle").classList.remove("d-block");
      clearTimeout(timeout);
    };
  };
  if (document.getElementById("layout-menu")) {
    delay(document.getElementById("layout-menu"), function () {
      // not for small screen
      if (!Helpers.isSmallScreen()) {
        document.querySelector(".layout-menu-toggle").classList.add("d-block");
      }
    });
  }

  // Display in main menu when menu scrolls
  let menuInnerContainer = document.getElementsByClassName("menu-inner"),
    menuInnerShadow = document.getElementsByClassName("menu-inner-shadow")[0];
  if (menuInnerContainer.length > 0 && menuInnerShadow) {
    menuInnerContainer[0].addEventListener("ps-scroll-y", function () {
      if (this.querySelector(".ps__thumb-y").offsetTop) {
        menuInnerShadow.style.display = "block";
      } else {
        menuInnerShadow.style.display = "none";
      }
    });
  }

  // Init helpers & misc
  // --------------------

  // Init BS Tooltip
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]'),
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Accordion active class
  const accordionActiveFunction = function (e) {
    if (e.type == "show.bs.collapse" || e.type == "show.bs.collapse") {
      e.target.closest(".accordion-item").classList.add("active");
    } else {
      e.target.closest(".accordion-item").classList.remove("active");
    }
  };

  const accordionTriggerList = [].slice.call(
    document.querySelectorAll(".accordion"),
  );
  const accordionList = accordionTriggerList.map(function (accordionTriggerEl) {
    accordionTriggerEl.addEventListener(
      "show.bs.collapse",
      accordionActiveFunction,
    );
    accordionTriggerEl.addEventListener(
      "hide.bs.collapse",
      accordionActiveFunction,
    );
  });

  // Auto update layout based on screen size
  window.Helpers.setAutoUpdate(true);

  // Toggle Password Visibility
  window.Helpers.initPasswordToggle();

  // Speech To Text
  window.Helpers.initSpeechToText();

  // Manage menu expanded/collapsed with templateCustomizer & local storage
  //------------------------------------------------------------------

  // If current layout is horizontal OR current window screen is small (overlay menu) than return from here
  if (window.Helpers.isSmallScreen()) {
    return;
  }

  // If current layout is vertical and current window screen is > small

  // Auto update menu collapsed/expanded based on the themeConfig
  window.Helpers.setCollapsed(true, false);
})();

function normalizePathName(pathValue) {
  const safePath = String(pathValue || "")
    .split("?")[0]
    .split("#")[0];
  const trimmed = safePath.endsWith("/") ? safePath.slice(0, -1) : safePath;
  const fileName = trimmed.split("/").pop() || "index.html";
  return fileName.toLowerCase();
}

function updateActiveMenuByCurrentPage() {
  const menuRoot = document.getElementById("layout-menu");
  if (!menuRoot) {
    return;
  }

  const currentPage = normalizePathName(window.location.pathname);

  menuRoot
    .querySelectorAll(".menu-item.active")
    .forEach((item) => item.classList.remove("active"));
  menuRoot
    .querySelectorAll(".menu-item.open")
    .forEach((item) => item.classList.remove("open"));

  const menuLinks = menuRoot.querySelectorAll("a.menu-link[href]");
  let matchedLink = null;

  menuLinks.forEach((link) => {
    const href = link.getAttribute("href") || "";
    if (!href || href.startsWith("javascript:") || href.startsWith("#")) {
      return;
    }

    if (normalizePathName(href) === currentPage) {
      matchedLink = link;
    }
  });

  if (!matchedLink) {
    return;
  }

  let menuItem = matchedLink.closest(".menu-item");
  while (menuItem) {
    menuItem.classList.add("active");
    if (menuItem.querySelector(":scope > .menu-sub")) {
      menuItem.classList.add("open");
    }
    menuItem = menuItem.parentElement.closest(".menu-item");
  }
}

function forceMenuLinksOpenInSameTab() {
  const menuRoot = document.getElementById("layout-menu");
  if (!menuRoot) {
    return;
  }

  menuRoot.querySelectorAll("a.menu-link[href]").forEach((link) => {
    const href = link.getAttribute("href") || "";
    if (!href || href.startsWith("javascript:") || href.startsWith("#")) {
      return;
    }

    link.setAttribute("target", "_self");
  });
}

function addDelayedMenuNavigation() {
  const menuRoot = document.getElementById("layout-menu");
  if (!menuRoot) {
    return;
  }

  menuRoot.querySelectorAll("a.menu-link[href]").forEach((link) => {
    const href = link.getAttribute("href") || "";
    if (!href || href.startsWith("javascript:") || href.startsWith("#")) {
      return;
    }

    link.addEventListener("click", function (event) {
      if (
        event.defaultPrevented ||
        event.button !== 0 ||
        event.metaKey ||
        event.ctrlKey ||
        event.shiftKey ||
        event.altKey
      ) {
        return;
      }

      event.preventDefault();
      document.body.style.cursor = "progress";

      setTimeout(function () {
        window.location.href = href;
      }, MENU_NAV_DELAY_MS);
    });
  });
}

function hideAdminMenuForNonAdmin() {
  const menuRoot = document.getElementById("layout-menu");
  if (!menuRoot) {
    return;
  }

  let rawUserInfo = null;
  try {
    rawUserInfo = localStorage.getItem("user_info");
  } catch (error) {
    rawUserInfo = null;
  }

  if (!rawUserInfo) {
    return;
  }

  let userInfo = null;
  try {
    userInfo = JSON.parse(rawUserInfo);
  } catch (error) {
    return;
  }

  const userRole = String(userInfo && userInfo.role ? userInfo.role : "")
    .trim()
    .toUpperCase();

  if (userRole === "ADMIN") {
    return;
  }

  const menuHeaders = Array.from(menuRoot.querySelectorAll(".menu-header"));
  const adminHeader = menuHeaders.find((header) => {
    const headerText = header.textContent || "";
    return headerText.trim().toUpperCase() === "ADMIN";
  });

  if (!adminHeader) {
    return;
  }

  adminHeader.style.display = "none";

  let nextNode = adminHeader.nextElementSibling;
  while (nextNode && !nextNode.classList.contains("menu-header")) {
    const currentNode = nextNode;
    nextNode = nextNode.nextElementSibling;
    currentNode.style.display = "none";
  }
}

document.addEventListener("DOMContentLoaded", function () {
  hideAdminMenuForNonAdmin();
  forceMenuLinksOpenInSameTab();
  addDelayedMenuNavigation();
  updateActiveMenuByCurrentPage();
});

function logout() {
  $.ajax({
    url: "http://localhost:5000/api/auth/logout",
    type: "POST",
    xhrFields: { withCredentials: true },
    complete: function () {
      localStorage.removeItem("user_info");
      window.location.href = "login.html";
    },
  });
}
