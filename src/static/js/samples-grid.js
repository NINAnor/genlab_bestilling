var inputRow = {};
let rowData = [];
let api = null;

function isPinnedRowDataCompleted(params) {
  if (params.rowPinned !== "top") return;
  return true;
  //return columnDefs.every((def) => inputRow[def.field]);
}

const gridOptions = {
  columnDefs: [
    { field: "guid", editable: true, checkboxSelection: true },
    { field: "type", editable: true },
    { field: "species", editable: true },
    { field: "markers", editable: true },
    { field: "date", editable: true, cellEditor: "agDateStringCellEditor" },
    { field: "pop_id", editable: true },
    { field: "area", editable: true },
    { field: "location", editable: true },
    {
      field: "volume",
      editable: true,
      cellEditor: "agNumberCellEditor",
      cellEditorParams: {
        precision: 2,
        preventStep: true,
      },
    },
    { field: "notes", editable: true },
    {
      field: "deleted",
      editable: true,
      cellRenderer: "agCheckboxCellRenderer",
      cellEditor: "agCheckboxCellEditor",
    },
  ],
  rowClassRules: {
    "bg-red": (params) => params.data.deleted,
  },
  editType: "fullRow",
  rowSelection: "multiple",
  rowData: [],
  onRowEditingStopped: (params) => {
    console.log("ended");
    if (isPinnedRowDataCompleted(params)) {
      // save data
      setRowData([...rowData, inputRow]);
      //reset pinned row
      setInputRow({});
    }
  },
  defaultColDef: {
    flex: 1,
    editable: true,
    valueFormatter: (params) =>
      isEmptyPinnedCell(params)
        ? createPinnedCellPlaceholder(params)
        : undefined,
  },
  pinnedTopRowData: [inputRow],
  getRowStyle: ({ node }) =>
    node.rowPinned ? { "font-weight": "bold", "font-style": "italic" } : 0,
};

function setRowData(newData) {
  rowData = newData;
  api.setRowData(rowData);
}

function setInputRow(newData) {
  inputRow = newData;
  api.setPinnedTopRowData([inputRow]);
}

function isEmptyPinnedCell({ node, value }) {
  return (
    (node.rowPinned === "top" && value == null) ||
    (node.rowPinned === "top" && value == "")
  );
}

function createPinnedCellPlaceholder({ colDef }) {
  return colDef.field[0].toUpperCase() + colDef.field.slice(1) + "...";
}

// Your Javascript code to create the data grid
const myGridElement = document.querySelector("#app");
api = agGrid.createGrid(myGridElement, gridOptions);
