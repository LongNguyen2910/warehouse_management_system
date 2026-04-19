function getStoredUserInfo() {
  const rawUserInfo = localStorage.getItem("user_info");

  if (!rawUserInfo) {
    return null;
  }

  try {
    return JSON.parse(rawUserInfo);
  } catch (error) {
    return null;
  }
}

function fillCurrentUser() {
  const userNameEl = document.getElementById("user_name");
  const userRoleEl = document.getElementById("user_role");
  const userInfo = getStoredUserInfo();

  if (!userInfo || !userNameEl || !userRoleEl) {
    return;
  }

  userNameEl.textContent = userInfo.username || "Unknown User";
  userRoleEl.textContent = userInfo.role || "No Role";
}

function bindLogout() {
  const logoutBtn = document.getElementById("log_out");
  if (!logoutBtn) {
    return;
  }

  logoutBtn.addEventListener("click", async function () {
    try {
      await fetch("http://localhost:5000/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } catch (error) {
      // Even if API call fails, local auth data still needs to be cleared.
    } finally {
      localStorage.removeItem("user_info");
      window.location.href = "../html/login.html";
    }
  });
}

async function clearUserInfoIfTokenMissing() {
  try {
    const response = await fetch("http://localhost:5000/api/roles", {
      method: "GET",
      credentials: "include",
    });

    if (response.status === 401) {
      localStorage.removeItem("user_info");
      window.location.href = "../html/login.html";
      return false;
    }
  } catch (error) {
    // Keep existing UI state on transient network failures.
  }

  return true;
}

document.addEventListener("DOMContentLoaded", async function () {
  const canContinue = await clearUserInfoIfTokenMissing();
  if (!canContinue) {
    return;
  }

  fillCurrentUser();
  bindLogout();
});
