import { useEffect, useMemo, useState } from "react";
import DatePicker from "react-datepicker";
import { createPortal } from "react-dom";

const datePortal = document.getElementById('date-portal');

export default function DateCell({ getValue, row: { original }, column: { id }, table }) {
  const initialValue = getValue() || "";
  // We need to keep and update the state of the cell normally
  const initialDate = useMemo(() => new Date(initialValue), [initialValue]);
  const [value, setValue] = useState(initialDate);

  // When the input is blurred, we'll call our table meta's updateData function
  const onBlur = () => {
    if (value !== initialValue) {
      table.options.meta?.updateData({ id: original.id, [id]: value.toLocaleDateString("en-US") });
    }
  };

  // If the initialValue is changed external, sync it up with our state
  useEffect(() => {
    setValue(initialValue || "");
  }, [initialValue]);

  return (
    <DatePicker
      selected={value}
      onChange={(e) => setValue(e)}
      onBlur={onBlur}
      dateFormat="dd/MM/YYYY"
      popperContainer={({children}) => createPortal(children, datePortal)}
    />
  );
}
