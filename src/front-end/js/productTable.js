let url = "http://localhost:5000/api";

$(document).ready(function () {
  getAllProducts();
  checkToastMessage();
});

/* ───────────── TOAST TỪ QUERY STRING ───────────── */
function checkToastMessage() {
  const params = new URLSearchParams(window.location.search);
  const msg = params.get("toast");
  if (msg) {
    showToast(decodeURIComponent(msg), "success");
    history.replaceState(null, "", window.location.pathname);
  }
}

/* ───────────── GET ALL ───────────── */
function getAllProducts() {
  $.ajax({
    url: url + "/products/",
    method: "GET",
    xhrFields: {
      withCredentials: true,
    },
    success: function (res) {
      const list = res;
      let table = "";

      if (list.length === 0) {
        table =
          '<tr><td colspan="7" class="text-center text-muted py-4">Không có sản phẩm nào.</td></tr>';
      }

      for (var i = 0; i < list.length; ++i) {
        const p = list[i];
        table += "<tr>";
        table +=
          '<td><i class="fab fa-react fa-lg text-info"></i> <strong>' +
          p.sku +
          "</strong></td>";
        table += "<td>" + p.product_name + "</td>";
        table += "<td>" + (p.category_name || "") + "</td>";
        table += "<td>" + p.min_stock + "</td>";
        table += "<td>" + (p.description || "") + "</td>";
        table += "<td>" + (p.created_at || "") + "</td>";
        table += "<td>";
        table += '<div class="dropdown">';
        table +=
          '<button type="button" class="btn p-0 dropdown-toggle hide-arrow" data-bs-toggle="dropdown">';
        table += '<i class="bx bx-dots-vertical-rounded"></i></button>';
        table += '<div class="dropdown-menu">';
        table +=
          '<a class="dropdown-item" href="javascript:void(0);" onclick="goToEdit(\'' +
          p.id +
          "')\">";
        table += '<i class="bx bx-edit-alt me-2"></i>Edit</a>';
        table +=
          '<a class="dropdown-item text-danger" href="javascript:void(0);" onclick="confirmDelete(\'' +
          p.id +
          "','" +
          escapeQuote(p.product_name) +
          "')\">";
        table += '<i class="bx bx-trash me-2"></i>Delete</a>';
        table += "</div></div>";
        table += "</td>";
        table += "</tr>";
      }

      document.getElementById("productsTableBody").innerHTML = table;
    },
    error: function (xhr) {
      if (xhr.status === 401) {
        logout();
        return;
      }
      showToast(
        "Lỗi tải danh sách: " + (xhr.responseJSON.message || xhr.statusText),
        "danger",
      );
    },
  });
}

/* ───────────── SỬA — chuyển trang ───────────── */
function goToEdit(id) {
  window.location.href = "product-form.html?id=" + id;
}

/* ───────────── XÓA — modal xác nhận ───────────── */
function confirmDelete(id, productName) {
  if (!document.getElementById("deleteModal")) {
    document.body.insertAdjacentHTML(
      "beforeend",
      `
            <div class="modal fade" id="deleteModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="bx bx-trash text-danger me-1"></i> Xác nhận xóa
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body" id="deleteModalBody"></div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Hủy</button>
                            <button type="button" class="btn btn-danger" id="btnConfirmDelete">
                                <i class="bx bx-trash me-1"></i>Xóa
                            </button>
                        </div>
                    </div>
                </div>
            </div>`,
    );
  }

  document.getElementById("deleteModalBody").innerHTML =
    '<p class="mb-0">Bạn có chắc muốn xóa sản phẩm <strong>' +
    productName +
    "</strong>?</p>";

  const btnDelete = document.getElementById("btnConfirmDelete");
  btnDelete.disabled = false;
  btnDelete.innerHTML = '<i class="bx bx-trash me-1"></i>Xóa';
  btnDelete.onclick = function () {
    executeDelete(id, productName);
  };

  new bootstrap.Modal(document.getElementById("deleteModal")).show();
}

/* ───────────── XÓA — gọi API ───────────── */
function executeDelete(id, productName) {
  const btnDelete = document.getElementById("btnConfirmDelete");
  btnDelete.disabled = true;
  btnDelete.innerHTML =
    '<span class="spinner-border spinner-border-sm me-1"></span>Đang xóa...';

  $.ajax({
    url: url + "/products/" + id,
    method: "DELETE",
    xhrFields: {
      withCredentials: true,
    },
    success: function () {
      bootstrap.Modal.getInstance(
        document.getElementById("deleteModal"),
      ).hide();
      showToast(
        "Xóa sản phẩm <strong>" + productName + "</strong> thành công!",
        "success",
      );
      getAllProducts();
    },
    error: function (xhr) {
      if (xhr.status === 401) {
        logout();
        return;
      }
      const res = xhr.responseJSON;

      if (xhr.status === 409 && res.error_code === "DB_FOREIGN_KEY_CONFLICT") {
        document.getElementById("deleteModalBody").innerHTML = `
                      <p>Không thể xóa sản phẩm <strong>${productName}</strong>.</p>
                      <div class="alert alert-warning mb-0">
                          <i class="bx bx-error-circle me-1"></i>
                          <strong>${res.message}</strong>
                          <div class="mt-1"><small>Vui lòng xóa dữ liệu liên quan trước rồi thử lại.</small></div>
                      </div>`;
        btnDelete.disabled = true;
        btnDelete.innerHTML = '<i class="bx bx-trash me-1"></i>Xóa';
      } else {
        document.getElementById("deleteModalBody").innerHTML = `
                    <p>Xóa sản phẩm <strong>${productName}</strong> thất bại.</p>
                    <div class="alert alert-danger mb-0">
                        <i class="bx bx-error me-1"></i>
                        ${res?.message || "Lỗi không xác định, vui lòng thử lại."}
                    </div>`;
        btnDelete.disabled = false;
        btnDelete.innerHTML = '<i class="bx bx-trash me-1"></i>Thử lại';
        btnDelete.onclick = function () {
          executeDelete(id, productName);
        };
      }
    },
  });
}

/* ───────────── TOAST THÔNG BÁO ───────────── */
function showToast(message, type = "success") {
  if (!document.getElementById("toastContainer")) {
    const container = document.createElement("div");
    container.id = "toastContainer";
    container.style.cssText =
      "position:fixed;top:20px;right:20px;z-index:9999;min-width:280px;";
    document.body.appendChild(container);
  }

  const id = "toast_" + Date.now();
  const iconMap = {
    success: "bx-check-circle",
    danger: "bx-error-circle",
    warning: "bx-error",
  };
  const icon = iconMap[type] || "bx-info-circle";

  document.getElementById("toastContainer").insertAdjacentHTML(
    "beforeend",
    `
        <div id="${id}" class="toast align-items-center text-bg-${type} border-0 mb-2 show" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bx ${icon} me-1"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="document.getElementById('${id}').remove()"></button>
            </div>
        </div>`,
  );

  setTimeout(function () {
    const el = document.getElementById(id);
    if (el) el.remove();
  }, 3500);
}

/* ───────────── HELPER ───────────── */
function escapeQuote(str) {
  return (str || "").replace(/'/g, "\\'");
}
