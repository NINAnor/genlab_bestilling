import { useCallback, useState } from "react";

export default function ActionsCell({ table, row: { original } }) {
  const [running, setRunning] = useState(false);

  const runDelete = useCallback(async () => {
    setRunning(true);
    await table.options.meta?.deleteRow({ id: original.id });
    setRunning(false);
  }, [original.id, table.options]);

  return (
    <div className="flex">
      <button
        disabled={running}
        className="btn bg-red-500 text-white rounded"
        onClick={runDelete}
      >
        <i className={`fas ${running ? "fa-spin fa-spinner" : "fa-trash"}`}></i>
      </button>
    </div>
  );
}
