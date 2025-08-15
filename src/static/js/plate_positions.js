function platePositions() {
  return {
    selectedPosition: null,
    selectedCoordinate: "",
    actions: [],
    loading: false,
    message: "",
    messageType: "success",
    showNotesEdit: false,
    notesInput: "",
    showSampleDetails: false,
    sampleDetails: null,
    loadingSample: false,
    showSampleSelection: false,
    selectedSampleId: null,
    showSampleMarkerSelection: false,
    selectedSampleMarkerId: null,

    async selectPosition(positionId, coordinate) {
      if (this.selectedPosition && this.selectedPosition.id === positionId) {
        return; // Already selected
      }

      this.selectedPosition = { id: positionId };
      this.selectedCoordinate = coordinate;
      this.loading = true;
      this.actions = [];
      this.message = "";
      this.showNotesEdit = false;

      try {
        const response = await fetch(`/api/plate-positions/${positionId}/`);
        if (response.ok) {
          const data = await response.json();
          this.selectedPosition = data;
          this.actions = data.possible_actions || [];
          this.notesInput = data.notes || "";
        } else {
          console.error(
            "Failed to load position details:",
            response.status,
            response.statusText
          );
          const errorData = await response.json().catch(() => ({}));
          console.error("Error response:", errorData);
          this.showMessage("Failed to load position details", "error");
        }
      } catch (error) {
        console.error("Error loading position details:", error);
        this.showMessage("Error loading position details", "error");
      } finally {
        this.loading = false;
      }
    },

    async performAction(actionType) {
      if (actionType === "edit_notes") {
        this.showNotesEdit = true;
        return;
      }

      if (actionType === "view_sample") {
        await this.viewSample();
        return;
      }

      if (actionType === "view_analysis") {
        await this.viewAnalysis();
        return;
      }

      if (actionType === "add_sample") {
        this.initSampleSelection();
        return;
      }

      if (actionType === "add_sample_marker") {
        this.initSampleMarkerSelection();
        return;
      }

      this.loading = true;
      this.message = "";

      try {
        const response = await fetch(
          `/api/plate-positions/${this.selectedPosition.id}/${actionType}/`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": document.querySelector(
                "[name=csrfmiddlewaretoken]"
              ).value,
            },
          }
        );

        if (response.ok) {
          const data = await response.json();
          this.showMessage(data.message, "success");
          // Refresh the position data
          await this.selectPosition(
            this.selectedPosition.id,
            this.selectedCoordinate
          );
          // Reload the page to update the grid
          setTimeout(() => window.location.reload(), 10);
        } else {
          console.error("Action failed:", response.status, response.statusText);
          const errorData = await response.json().catch(() => ({}));
          console.error("Error response:", errorData);
          this.showMessage(errorData.error || "Action failed", "error");
        }
      } catch (error) {
        console.error("Error performing action:", error);
        this.showMessage("Error performing action", "error");
      } finally {
        this.loading = false;
      }
    },

    async saveNotes() {
      this.loading = true;

      try {
        const response = await fetch(
          `/api/plate-positions/${this.selectedPosition.id}/edit_notes/`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": document.querySelector(
                "[name=csrfmiddlewaretoken]"
              ).value,
            },
            body: JSON.stringify({ notes: this.notesInput }),
          }
        );

        if (response.ok) {
          const data = await response.json();
          this.showMessage(data.message, "success");
          this.showNotesEdit = false;
          this.selectedPosition.notes = this.notesInput;
        } else {
          console.error(
            "Failed to save notes:",
            response.status,
            response.statusText
          );
          const errorData = await response.json().catch(() => ({}));
          console.error("Error response:", errorData);
          this.showMessage(errorData.error || "Failed to save notes", "error");
        }
      } catch (error) {
        console.error("Error saving notes:", error);
        this.showMessage("Error saving notes", "error");
      } finally {
        this.loading = false;
      }
    },

    cancelNotesEdit() {
      this.showNotesEdit = false;
      this.notesInput = this.selectedPosition.notes || "";
    },

    async viewSample() {
      if (!this.selectedPosition.sample_raw) {
        this.showMessage("No sample to view", "error");
        return;
      }

      this.loadingSample = true;
      this.sampleDetails = null;

      try {
        const response = await fetch(
          `/api/samples/${this.selectedPosition.sample_raw.id}/`
        );
        if (response.ok) {
          const data = await response.json();
          this.sampleDetails = data;
          this.showSampleDetails = true;
        } else {
          console.error(
            "Failed to load sample details:",
            response.status,
            response.statusText
          );
          const errorData = await response.json().catch(() => ({}));
          console.error("Error response:", errorData);
          this.showMessage("Failed to load sample details", "error");
        }
      } catch (error) {
        console.error("Error loading sample details:", error);
        this.showMessage("Error loading sample details", "error");
      } finally {
        this.loadingSample = false;
      }
    },

    async viewAnalysis() {
      if (!this.selectedPosition.sample_marker) {
        this.showMessage("No analysis to view", "error");
        return;
      }

      this.loadingSample = true;
      this.sampleDetails = null;

      try {
        const response = await fetch(
          `/api/sample-marker-analysis/${this.selectedPosition.sample_marker.id}/`
        );
        if (response.ok) {
          const data = await response.json();
          this.sampleDetails = data;
          this.showSampleDetails = true;
        } else {
          console.error(
            "Failed to load analysis details:",
            response.status,
            response.statusText
          );
          const errorData = await response.json().catch(() => ({}));
          console.error("Error response:", errorData);
          this.showMessage("Failed to load analysis details", "error");
        }
      } catch (error) {
        console.error("Error loading analysis details:", error);
        this.showMessage("Error loading analysis details", "error");
      } finally {
        this.loadingSample = false;
      }
    },

    closeSampleDetails() {
      this.showSampleDetails = false;
      this.sampleDetails = null;
    },

    getPositionStatus() {
      if (!this.selectedPosition) return "";

      if (this.selectedPosition.sample_raw) {
        return `Contains sample: ${this.selectedPosition.sample_raw.genlab_id}`;
      } else if (this.selectedPosition.sample_marker) {
        return `Contains analysis: ${this.selectedPosition.sample_marker.id}`;
      } else if (this.selectedPosition.is_reserved) {
        return "Reserved";
      } else {
        return "Empty position";
      }
    },

    getActionButtonClass(type) {
      const baseClasses = "transition-colors";
      switch (type) {
        case "success":
          return baseClasses + " bg-green-600 text-white hover:bg-green-700";
        case "danger":
          return baseClasses + " bg-red-600 text-white hover:bg-red-700";
        case "warning":
          return baseClasses + " bg-yellow-600 text-white hover:bg-yellow-700";
        case "info":
          return baseClasses + " bg-blue-600 text-white hover:bg-blue-700";
        default:
          return baseClasses + " bg-gray-600 text-white hover:bg-gray-700";
      }
    },

    showMessage(msg, type = "success") {
      this.message = msg;
      this.messageType = type;
      setTimeout(() => {
        this.message = "";
      }, 5000);
    },

    initSampleSelection() {
      this.selectedSampleId = null;
      this.showSampleSelection = true;

      // Initialize Select2 after modal is shown
      this.$nextTick(() => {
        $("#sample-select")
          .select2({
            ajax: {
              url: $("#sample-select").data("url"),
              dataType: "json",
              delay: 250,
              data: (params) => {
                return {
                  q: params.term, // Search term
                  page: params.page || 1, // Pagination
                };
              },
              processResults: (data, params) => {
                params.page = params.page || 1;
                return {
                  results: data.results,
                  pagination: {
                    more: data.next ? true : false,
                  },
                };
              },
            },
          })
          .on("change", (e) => {
            this.selectedSampleId = $(e.target).val();
          });
      });
    },

    closeSampleSelection() {
      this.showSampleSelection = false;
      this.selectedSampleId = null;

      // Destroy Select2 to clean up
      if ($("#sample-select").hasClass("select2-hidden-accessible")) {
        $("#sample-select").select2("destroy");
      }
    },

    async addSelectedSample() {
      if (!this.selectedSampleId) {
        this.showMessage("Please select a sample", "error");
        return;
      }

      this.loading = true;

      try {
        const response = await fetch(
          `/api/plate-positions/${this.selectedPosition.id}/add_sample/`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": document.querySelector(
                "[name=csrfmiddlewaretoken]"
              ).value,
            },
            body: JSON.stringify({ sample_id: this.selectedSampleId }),
          }
        );

        if (response.ok) {
          const data = await response.json();
          this.showMessage(data.message, "success");
          this.closeSampleSelection();
          // Refresh the position data
          await this.selectPosition(
            this.selectedPosition.id,
            this.selectedCoordinate
          );
          // Reload the page to update the grid
          setTimeout(() => window.location.reload(), 10);
        } else {
          console.error(
            "Failed to add sample:",
            response.status,
            response.statusText
          );
          const errorData = await response.json().catch(() => ({}));
          console.error("Error response:", errorData);
          this.showMessage(errorData.error || "Failed to add sample", "error");
        }
      } catch (error) {
        console.error("Error adding sample:", error);
        this.showMessage("Error adding sample", "error");
      } finally {
        this.loading = false;
      }
    },

    initSampleMarkerSelection() {
      this.selectedSampleMarkerId = null;
      this.showSampleMarkerSelection = true;

      // Initialize Select2 after modal is shown
      this.$nextTick(() => {
        $("#sample-marker-select")
          .select2({
            ajax: {
              url: $("#sample-marker-select").data("url"),
              dataType: "json",
              delay: 250,
              data: (params) => {
                return {
                  q: params.term, // Search term
                  page: params.page || 1, // Pagination
                };
              },
              processResults: (data, params) => {
                params.page = params.page || 1;
                return {
                  results: data.results,
                  pagination: {
                    more: data.next ? true : false,
                  },
                };
              },
            },
          })
          .on("change", (e) => {
            this.selectedSampleMarkerId = $(e.target).val();
          });
      });
    },

    closeSampleMarkerSelection() {
      this.showSampleMarkerSelection = false;
      this.selectedSampleMarkerId = null;

      // Destroy Select2 to clean up
      if ($("#sample-marker-select").hasClass("select2-hidden-accessible")) {
        $("#sample-marker-select").select2("destroy");
      }
    },

    async addSelectedSampleMarker() {
      if (!this.selectedSampleMarkerId) {
        this.showMessage("Please select a sample marker", "error");
        return;
      }

      this.loading = true;

      try {
        const response = await fetch(
          `/api/plate-positions/${this.selectedPosition.id}/add_sample_marker/`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": document.querySelector(
                "[name=csrfmiddlewaretoken]"
              ).value,
            },
            body: JSON.stringify({
              sample_marker_id: this.selectedSampleMarkerId,
            }),
          }
        );

        if (response.ok) {
          const data = await response.json();
          this.showMessage(data.message, "success");
          this.closeSampleMarkerSelection();
          // Refresh the position data
          await this.selectPosition(
            this.selectedPosition.id,
            this.selectedCoordinate
          );
          // Reload the page to update the grid
          setTimeout(() => window.location.reload(), 10);
        } else {
          console.error(
            "Failed to add sample marker:",
            response.status,
            response.statusText
          );
          const errorData = await response.json().catch(() => ({}));
          console.error("Error response:", errorData);
          this.showMessage(
            errorData.error || "Failed to add sample marker",
            "error"
          );
        }
      } catch (error) {
        console.error("Error adding sample marker:", error);
        this.showMessage("Error adding sample marker", "error");
      } finally {
        this.loading = false;
      }
    },
  };
}
