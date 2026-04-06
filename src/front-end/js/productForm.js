let url = "http://localhost:5000/api";

const params = new URLSearchParams(window.location.search);
const editId = params.get("id");

$(document).ready(function () {
  displayCategory();

  if (editId) {
    // Chế độ sửa
    document.querySelector(".card-header h5").textContent = "Edit Product";
    document.querySelector('button[type="submit"]').textContent = "Update";
    loadProduct(editId);
  }

  $("form").on("submit", function (e) {
    e.preventDefault();
    submitForm();
  });
});

function displayCategory() {
  $.ajax({
    url: url + "/categories/",
    method: "GET",
    xhrFields: {
      withCredentials: true,
    },
    error: function (xhr) {
      if (xhr.status === 401) {
        logout();
        return;
      }
      alert($.ajax.error);
    },
    success: function (res) {
      res = res.data;
      const len = res.length;
      console.log(len);
      let table = '<option value="">None</option>';
      for (var i = 0; i < len; ++i) {
        table +=
          '<option value="' + res[i].name + '">' + res[i].name + "</option>";
      }
      document.getElementById("categorySelect").innerHTML = table;

      if (editId) {
        loadProduct(editId);
      }
    },
    fail: function (response) {},
  });
}

function loadProduct(id) {
  $.ajax({
    url: url + "/products/" + id,
    method: "GET",
    xhrFields: {
      withCredentials: true,
    },
    success: function (res) {
      const p = res.data || res;

      document.getElementById("basic-default-sku").value = p.sku || "";
      document.getElementById("basic-default-product-name").value =
        p.product_name || "";
      document.getElementById("basic-default-min-stock").value =
        p.min_stock || 0;
      document.getElementById("basic-default-description").value =
        p.description || "";

      // Set category — phải set sau khi options đã render
      document.getElementById("categorySelect").value = p.category_id || "";

      // Set created_at — format về "YYYY-MM-DDTHH:mm" cho input datetime-local
      document.getElementById("basic-default-created-at").value =
        formatDatetimeLocal(p.created_at);
    },
    error: function (res) {
      if (res.status === 401) {
        logout();
        return;
      }
      showAlert("Không tải được thông tin sản phẩm.", "danger");
    },
  });
}

/* ───────────── Validate ───────────── */
function validate() {
  const sku = document.getElementById("basic-default-sku").value.trim();
  const name = document
    .getElementById("basic-default-product-name")
    .value.trim();
  const category = document.getElementById("categorySelect").value;

  if (!sku) {
    showAlert("Vui lòng nhập SKU.", "warning");
    return false;
  }
  if (!name) {
    showAlert("Vui lòng nhập tên sản phẩm.", "warning");
    return false;
  }
  if (!category) {
    showAlert("Vui lòng chọn danh mục.", "warning");
    return false;
  }
  return true;
}

/* ───────────── Submit ───────────── */
function submitForm() {
  if (!validate()) return;

  const createdAtRaw = document.getElementById(
    "basic-default-created-at",
  ).value;

  const data = {
    sku: document.getElementById("basic-default-sku").value.trim(),
    product_name: document
      .getElementById("basic-default-product-name")
      .value.trim(),
    category_name: document.getElementById("categorySelect").value, // gửi number, không phải string
    min_stock:
      parseInt(document.getElementById("basic-default-min-stock").value) || 0,
    description: document
      .getElementById("basic-default-description")
      .value.trim(),
    created_at: createdAtRaw ? createdAtRaw + ":00" : null, // thêm ":00" giây cho đúng format backend
  };

  console.log("Sending data:", data); // debug — xem data gửi đi

  const isEdit = !!editId;
  const apiUrl = isEdit ? url + "/products/" + editId : url + "/products/";
  const method = isEdit ? "PUT" : "POST";

  const btnSubmit = document.querySelector('button[type="submit"]');
  btnSubmit.disabled = true;
  btnSubmit.innerHTML =
    '<span class="spinner-border spinner-border-sm me-1"></span>Đang lưu...';

  $.ajax({
    url: apiUrl,
    method: method,
    xhrFields: {
      withCredentials: true,
    },
    contentType: "application/json",
    data: JSON.stringify(data),
    success: function () {
      const msg = isEdit
        ? "Cập nhật sản phẩm thành công!"
        : "Thêm sản phẩm thành công!";
      window.location.href =
        "product-table.html?toast=" + encodeURIComponent(msg);
    },
    error: function (xhr) {
      if (xhr.status === 401) {
        logout();
        return;
      }
      console.log("Error response:", xhr.responseJSON); // debug — xem backend trả về lỗi gì
      const msg = xhr.responseJSON.message || "Lưu thất bại, vui lòng thử lại.";
      showAlert(msg, "danger");

      btnSubmit.disabled = false;
      btnSubmit.textContent = isEdit ? "Update" : "Send";
    },
  });
}

/* ───────────── Helper: format datetime-local ───────────── */
function formatDatetimeLocal(datetimeStr) {
  if (!datetimeStr) return "";
  // Xử lý cả dạng "2024-01-15 08:30:00" lẫn "2024-01-15T08:30:00"
  const normalized = datetimeStr.replace(" ", "T");
  return normalized.slice(0, 16); // lấy "YYYY-MM-DDTHH:mm"
}

/* ───────────── Alert inline ───────────── */
function showAlert(message, type = "danger") {
  const existing = document.getElementById("formAlert");
  if (existing) existing.remove();

  const alertHtml = `
        <div id="formAlert" class="alert alert-${type} alert-dismissible fade show mb-3" role="alert">
            <i class="bx bx-${type === "danger" ? "error" : "error-circle"} me-1"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>`;

  document
    .querySelector(".card-body form")
    .insertAdjacentHTML("afterbegin", alertHtml);

  setTimeout(function () {
    const el = document.getElementById("formAlert");
    if (el) el.remove();
  }, 4000);
}
