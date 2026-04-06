let url = "http://localhost:5000/api";
let receiptType = "inbound";
let productsList = [];
let productOptions = [];

$(document).ready(function () {
  const params = new URLSearchParams(window.location.search);
  receiptType = params.get("type") || "inbound";

  if (receiptType === "inbound") {
    $("#formTitle").html(
      '<i class="bx bx-import text-success"></i> Tạo phiếu nhập',
    );
  } else {
    $("#formTitle").html(
      '<i class="bx bx-export text-danger"></i> Tạo phiếu xuất',
    );
  }

  loadWarehouses();
  loadStaff();
  loadProducts();
  addProductRow();

  $("#receiptForm").on("submit", function (e) {
    e.preventDefault();
    submitReceipt();
  });
});

function loadWarehouses() {
  $.ajax({
    url: url + "/warehouses/",
    xhrFields: { withCredentials: true },
    method: "GET",
    success: function (data) {
      // API warehouses trả về { success: true, data: [...] }
      const warehouses = data.data || data;
      let options = '<option value="">Chọn kho</option>';
      for (let i = 0; i < warehouses.length; i++) {
        options += `<option value="${warehouses[i].name}">${warehouses[i].name}</option>`;
      }
      $("#warehouse").html(options);
    },
    error: function (res) {
      if (res.status === 401) {
        logout();
        return;
      }
      $("#warehouse").html('<option value="">Lỗi tải dữ liệu</option>');
      showToast("Không thể tải danh sách kho", "danger");
    },
  });
}

function loadStaff() {
  $.ajax({
    url: url + "/users/",
    xhrFields: { withCredentials: true },
    method: "GET",
    success: function (data) {
      // API users trả về { success: true, data: [...] }
      const users = data.data || data;
      let options = '<option value="">Chọn nhân viên</option>';
      if (Array.isArray(users)) {
        for (let i = 0; i < users.length; i++) {
          options += `<option value="${users[i].username}">${users[i].username}</option>`;
        }
      }
      $("#staff").html(options);
    },
    error: function (xhr) {
      if (xhr.status === 401) {
        logout();
        return;
      }
      console.error("Lỗi tải staff:", xhr);
      $("#staff").html('<option value="">Lỗi tải dữ liệu</option>');
      showToast("Không thể tải danh sách nhân viên", "danger");
    },
  });
}

function loadProducts() {
  $.ajax({
    url: url + "/products/",
    xhrFields: { withCredentials: true },
    method: "GET",
    success: function (data) {
      // API products trả về mảng trực tiếp
      if (Array.isArray(data)) {
        productOptions = data;
      } else if (data.data && Array.isArray(data.data)) {
        productOptions = data.data;
      } else {
        productOptions = [];
      }
      console.log("Đã tải", productOptions.length, "sản phẩm");

      // Cập nhật lại các select đã có
      updateAllProductSelects();
    },
    error: function (xhr) {
      if (xhr.status === 401) {
        logout();
        return;
      }
      console.error("Lỗi tải sản phẩm:", xhr);
      showToast("Lỗi tải danh sách sản phẩm", "danger");
    },
  });
}

function updateAllProductSelects() {
  $(".product-select").each(function () {
    const index = $(this).data("index");
    const currentValue = $(this).val();

    let productHtml =
      '<select class="form-select product-select" data-index="' + index + '">';
    productHtml += '<option value="">Chọn sản phẩm</option>';
    for (let i = 0; i < productOptions.length; i++) {
      const selected =
        currentValue === productOptions[i].product_name ? "selected" : "";
      productHtml += `<option value="${productOptions[i].product_name}" ${selected}>${productOptions[i].sku} - ${productOptions[i].product_name}</option>`;
    }
    productHtml += "</select>";

    $(this).replaceWith(productHtml);

    $(`.product-select[data-index="${index}"]`).on("change", function () {
      productsList[index].product_name = $(this).val();
    });
  });
}

function addProductRow() {
  const index = productsList.length;
  productsList.push({ product_name: "", quantity: 0, price: 0 });

  let productHtml =
    '<select class="form-select product-select" data-index="' + index + '">';
  productHtml += '<option value="">Chọn sản phẩm</option>';

  if (productOptions && productOptions.length > 0) {
    for (let i = 0; i < productOptions.length; i++) {
      productHtml += `<option value="${productOptions[i].product_name}">${productOptions[i].sku} - ${productOptions[i].product_name}</option>`;
    }
  }
  productHtml += "</select>";

  const rowHtml = `
        <div class="product-row" id="productRow_${index}">
            <div class="row">
                <div class="col-md-5">
                    <label class="form-label small">Sản phẩm</label>
                    ${productHtml}
                </div>
                <div class="col-md-3">
                    <label class="form-label small">Số lượng</label>
                    <input type="number" class="form-control product-qty" data-index="${index}" value="0" min="1">
                </div>
                <div class="col-md-3">
                    <label class="form-label small">Đơn giá</label>
                    <input type="number" class="form-control product-price" data-index="${index}" value="0" min="0" step="1000">
                </div>
                <div class="col-md-1 text-end">
                    <label class="form-label small">&nbsp;</label>
                    <div><i class="bx bx-trash text-danger fs-5 remove-product" onclick="removeProductRow(${index})"></i></div>
                </div>
            </div>
        </div>
    `;

  $("#productsList").append(rowHtml);

  $(`.product-select[data-index="${index}"]`).on("change", function () {
    productsList[index].product_name = $(this).val();
  });

  $(`.product-qty[data-index="${index}"]`).on("input", function () {
    productsList[index].quantity = parseInt($(this).val()) || 0;
  });

  $(`.product-price[data-index="${index}"]`).on("input", function () {
    productsList[index].price = parseFloat($(this).val()) || 0;
  });
}

function removeProductRow(index) {
  $(`#productRow_${index}`).remove();
  productsList[index] = null;
}

function submitReceipt() {
  const warehouse = $("#warehouse").val();
  const staff = $("#staff").val();
  const partner = $("#partner").val().trim();

  if (!warehouse) {
    showToast("Vui lòng chọn kho!", "warning");
    return;
  }
  if (!staff) {
    showToast("Vui lòng chọn nhân viên!", "warning");
    return;
  }
  if (!partner) {
    showToast("Vui lòng nhập tên đối tác!", "warning");
    return;
  }

  const items = productsList.filter(
    (p) => p && p.product_name && p.quantity > 0,
  );

  if (items.length === 0) {
    showToast("Vui lòng thêm ít nhất một sản phẩm!", "warning");
    return;
  }

  const data = {
    warehouse_name: warehouse,
    staff_name: staff,
    partner_name: partner,
    items: items.map((item) => ({
      product_name: item.product_name,
      quantity: item.quantity,
      price: item.price,
    })),
  };

  console.log("📦 Đang gửi dữ liệu:", data);

  const apiUrl =
    receiptType === "inbound"
      ? url + "/receipts/inbound"
      : url + "/receipts/outbound";

  const $btn = $('button[type="submit"]');
  $btn
    .prop("disabled", true)
    .html(
      '<span class="spinner-border spinner-border-sm me-1"></span>Đang xử lý...',
    );

  $.ajax({
    url: apiUrl,
    xhrFields: { withCredentials: true },
    method: "POST",
    contentType: "application/json",
    data: JSON.stringify(data),
    success: function (response) {
      console.log("✅ Thành công:", response);
      showToast(
        receiptType === "inbound"
          ? "Tạo phiếu nhập thành công!"
          : "Tạo phiếu xuất thành công!",
        "success",
      );
      setTimeout(() => {
        window.location.href = "receipt-list.html";
      }, 1500);
    },
    error: function (xhr) {
      if (xhr.status === 401) {
        logout();
        return;
      }
      console.error("❌ Lỗi:", xhr);
      let errorMsg = "Lưu thất bại!";
      if (xhr.responseJSON && xhr.responseJSON.message) {
        errorMsg = xhr.responseJSON.message;
      } else if (xhr.status === 400) {
        errorMsg = xhr.responseText || "Dữ liệu không hợp lệ!";
      }
      showToast(errorMsg, "danger");
      $btn.prop("disabled", false).html("Lưu phiếu");
    },
  });
}

function showToast(message, type) {
  if (!$("#toastContainer").length) {
    $("body").append(
      '<div id="toastContainer" style="position:fixed;top:20px;right:20px;z-index:9999"></div>',
    );
  }

  const icon =
    type === "success"
      ? "bx-check-circle"
      : type === "danger"
        ? "bx-error-circle"
        : "bx-error";
  const bgClass =
    type === "success"
      ? "text-bg-success"
      : type === "danger"
        ? "text-bg-danger"
        : "text-bg-warning";

  const toastId = "toast_" + Date.now();
  $("#toastContainer").append(`
        <div id="${toastId}" class="toast align-items-center ${bgClass} border-0 mb-2 show" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bx ${icon} me-1"></i> ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="$('#${toastId}').remove()"></button>
            </div>
        </div>
    `);

  setTimeout(() => $(`#${toastId}`).remove(), 3000);
}
