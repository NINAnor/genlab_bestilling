import { useEffect, useState } from "react";


export default function NumberCellInput({ getValue, row: { original }, column: { id }, table }) {
  const initialValue = getValue() || "";
  // We need to keep and update the state of the cell normally
  const [value, setValue] = useState(initialValue);

  // When the input is blurred, we'll call our table meta's updateData function
  const onBlur = () => {
    if (value !== initialValue) {
      table.options.meta?.updateData({ id: original.id, [id]: value });
    }
  };

  // If the initialValue is changed external, sync it up with our state
  useEffect(() => {
    setValue(initialValue || "");
  }, [initialValue]);

  return (
    <input
      className="border-0 w-full"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      onBlur={onBlur}
      type="number"
    />
  );
}
