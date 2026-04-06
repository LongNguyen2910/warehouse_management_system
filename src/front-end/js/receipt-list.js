let url = "http://localhost:5000/api";

$(document).ready(function () {
  loadAllReceipts();
});

function loadAllReceipts() {
  loadInboundReceipts();
  loadOutboundReceipts();
}

function loadInboundReceipts() {
  $.ajax({
    url: url + "/receipts/inbound",
    method: "GET",
    xhrFields: { withCredentials: true },
    success: function (data) {
      displayReceipts(data, "inboundList", "inbound");
    },
    error: function (xhr) {
      if (xhr.status === 401) {
        logout();
        return;
      }
      $("#inboundList").html(
        '<div class="text-center text-danger py-4">Lỗi tải dữ liệu: ' +
          (xhr.responseJSON.message || xhr.statusText) +
          "</div>",
      );
    },
  });
}

function loadOutboundReceipts() {
  $.ajax({
    url: url + "/receipts/outbound",
    method: "GET",
    xhrFields: { withCredentials: true },
    success: function (data) {
      displayReceipts(data, "outboundList", "outbound");
    },
    error: function (xhr) {
      if (xhr.status === 401) {
        logout();
        return;
      }
      $("#outboundList").html(
        '<div class="text-center text-danger py-4">Lỗi tải dữ liệu: ' +
          (xhr.responseJSON.message || xhr.statusText) +
          "</div>",
      );
    },
  });
}

function displayReceipts(receipts, containerId, type) {
  const $container = $("#" + containerId);

  if (!receipts || receipts.length === 0) {
    $container.html(
      '<div class="text-center text-muted py-4">📭 Chưa có phiếu nào</div>',
    );
    return;
  }

  let html = "";
  for (let i = 0; i < receipts.length; i++) {
    const r = receipts[i];
    const totalItems = r.items ? r.items.length : 0;
    const totalQuantity = r.items
      ? r.items.reduce((sum, item) => sum + (item.qty || 0), 0)
      : 0;

    html += `
            <div class="receipt-card ${type === "inbound" ? "receipt-inbound" : "receipt-outbound"} card mb-3">
                <div class="receipt-header" onclick="toggleReceipt(${i}, '${containerId}')">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong class="fs-5">#${r.id}</strong>
                            <span class="badge ${type === "inbound" ? "badge-inbound" : "badge-outbound"} ms-2">
                                ${type === "inbound" ? "NHẬP" : "XUẤT"}
                            </span>
                        </div>
                        <div>
                            <small class="text-muted">${formatDate(r.created_at)}</small>
                            <i class="bx bx-chevron-down ms-2 toggle-icon" id="toggleIcon_${containerId}_${i}"></i>
                        </div>
                    </div>
                    <div class="row mt-2 small text-muted">
                        <div class="col-md-4"><i class="bx bx-buildings"></i> Kho: ${r.warehouse || r.warehouse_name || "-"}</div>
                        <div class="col-md-4"><i class="bx bx-user"></i> NV: ${r.staff || r.staff_name || "-"}</div>
                        <div class="col-md-4"><i class="bx bx-building"></i> Đối tác: ${r.partner || r.customer || r.partner_name || "-"}</div>
                    </div>
                    <div class="mt-1 small">
                        <span class="badge bg-secondary">${totalItems} sản phẩm</span>
                        <span class="badge bg-secondary ms-1">Tổng SL: ${totalQuantity}</span>
                    </div>
                </div>
                <div class="receipt-body" id="receiptBody_${containerId}_${i}">
                    <h6 class="mb-2">Chi tiết sản phẩm:</h6>
                    ${displayItems(r.items)}
                    <div class="mt-3 text-end">
                        <button class="btn btn-sm btn-danger" onclick="deleteReceipt(${r.id}, '${type}', event)">
                            <i class="bx bx-trash me-1"></i> Xóa phiếu
                        </button>
                    </div>
                </div>
            </div>
        `;
  }
  $container.html(html);
}

function displayItems(items) {
  if (!items || items.length === 0) {
    return '<div class="text-muted">Không có sản phẩm</div>';
  }

  let html = '<div class="list-group">';
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const totalPrice = (item.price || 0) * (item.qty || 0);
    html += `
            <div class="list-group-item product-item">
                <div class="row">
                    <div class="col-md-5"><strong>${item.product || item.product_name || "-"}</strong></div>
                    <div class="col-md-2">SL: ${item.qty || item.quantity || 0}</div>
                    <div class="col-md-3">ĐG: ${formatCurrency(item.price || 0)}</div>
                    <div class="col-md-2">TT: ${formatCurrency(totalPrice)}</div>
                </div>
            </div>
        `;
  }
  html += "</div>";
  return html;
}

function toggleReceipt(index, containerId) {
  const $body = $("#receiptBody_" + containerId + "_" + index);
  const $icon = $("#toggleIcon_" + containerId + "_" + index);

  $body.toggleClass("show");

  if ($body.hasClass("show")) {
    $icon.removeClass("bx-chevron-down").addClass("bx-chevron-up");
  } else {
    $icon.removeClass("bx-chevron-up").addClass("bx-chevron-down");
  }
}

function deleteReceipt(id, type, event) {
  event.stopPropagation();

  if (
    !confirm(`Bạn có chắc chắn muốn xóa phiếu ${type.toUpperCase()} #${id}?`)
  ) {
    return;
  }

  $.ajax({
    url: url + "/receipts/" + id,
    method: "DELETE",
    xhrFields: { withCredentials: true },
    success: function (response) {
      showToast("Xóa phiếu thành công!", "success");
      loadAllReceipts();
    },
    error: function (xhr) {
      if (xhr.status === 401) {
        logout();
        return;
      }
      let errorMsg = "Xóa thất bại!";
      if (xhr.status === 404) {
        errorMsg = "Không tìm thấy phiếu!";
      } else if (xhr.responseJSON && xhr.responseJSON.message) {
        errorMsg = xhr.responseJSON.message;
      }
      showToast(errorMsg, "danger");
    },
  });
}

function refreshData() {
  loadAllReceipts();
  showToast("Đã làm mới dữ liệu", "info");
}

function formatDate(dateString) {
  if (!dateString) return "-";
  try {
    const date = new Date(dateString);
    return (
      date.toLocaleDateString("vi-VN") + " " + date.toLocaleTimeString("vi-VN")
    );
  } catch (e) {
    return dateString;
  }
}

function formatCurrency(amount) {
  if (!amount) return "0 VND";
  return amount.toLocaleString("vi-VN") + " VND";
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
        : "bx-info-circle";
  const bgClass =
    type === "success"
      ? "text-bg-success"
      : type === "danger"
        ? "text-bg-danger"
        : "text-bg-info";

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
