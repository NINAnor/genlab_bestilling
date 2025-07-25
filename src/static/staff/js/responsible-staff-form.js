/**
 * Handles automatic submission of responsible staff form changes
 */
(function () {
  function initResponsibleStaffForm() {
    const forms = document.querySelectorAll(".responsible-staff-form");

    forms.forEach(function (form) {
      const select = form.querySelector("select");
      const updateUrl = form.dataset.updateUrl;

      if (!select || !updateUrl) {
        console.warn("Responsible staff form missing select or update URL");
        return;
      }

      $(select).on("change", function () {
        const selectedUserIds = $(this).val() || [];

        updateAssignedStaff(updateUrl, selectedUserIds)
          .then(function (_response) {
            console.log("Staff updated successfully");
          })
          .catch(function (error) {
            console.error("Error updating assigned staff:", error);
          });
      });
    });
  }

  async function updateAssignedStaff(updateUrl, userIds) {
    const csrfToken =
      document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
      document.querySelector("meta[name=csrf-token]")?.getAttribute("content");

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
    });
  }

  // Initialize when DOM is ready
  document.addEventListener("DOMContentLoaded", function () {
    initResponsibleStaffForm();
  });
})();
