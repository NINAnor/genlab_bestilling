function initResponsibleStaffForm() {
  const forms = document.querySelectorAll(".responsible-staff-form");

  forms.forEach(function (form) {
    const select = form.querySelector("select");
    const updateUrl = form.dataset.updateUrl;

    if (!select || !updateUrl) {
      console.warn("Responsible staff form missing select or update URL");
      return;
    }

    let currentAbortController = null;

    $(select).on("change", function () {
      const selectedUserIds = $(this).val() || [];

      // Cancel previous request if it exists
      if (currentAbortController) {
        currentAbortController.abort();
      }

      // Create new abort controller for this request
      currentAbortController = new AbortController();

      statusIndicator.showSpinner(form);

      updateAssignedStaff(
        updateUrl,
        selectedUserIds,
        currentAbortController.signal
      )
        .then(function (response) {
          if (!response.ok) {
            throw new Error("Could not update responsible staff");
          }

          statusIndicator.showSuccess(form);

          setTimeout(() => statusIndicator.hide(form), 2000);

          currentAbortController = null;
        })
        .catch(function (error) {
          // Only handle non-abort errors
          if (error.name !== "AbortError") {
            statusIndicator.showError(form);

            // Reload the page to reflect server-side changes
            setTimeout(() => {
              window.location.reload();
            }, 500);
          }

          currentAbortController = null;
        });
    });
  });
}

async function updateAssignedStaff(updateUrl, userIds, signal) {
  const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value;

  if (!csrfToken) {
    throw new Error("CSRF token not found");
  }

  return await fetch(updateUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify({
      user_ids: userIds,
    }),
    signal: signal,
  });
}

const statusIndicator = {
  hide: function (form) {
    const existing = form.querySelector(".staff-status-indicator");
    if (existing) {
      existing.remove();
    }
  },

  show: function (form, type, icon) {
    this.hide(form);
    const indicator = document.createElement("div");
    indicator.className = `staff-status-indicator ${type}`;
    indicator.innerHTML = `<i class="fas ${icon}"></i>`;
    form.appendChild(indicator);
  },

  showSpinner: function (form) {
    this.show(form, "spinner", "fa-spinner fa-spin");
  },

  showSuccess: function (form) {
    this.show(form, "success", "fa-check");
  },

  showError: function (form) {
    this.show(form, "error", "fa-times");
  },
};

document.addEventListener("DOMContentLoaded", function () {
  initResponsibleStaffForm();
});
