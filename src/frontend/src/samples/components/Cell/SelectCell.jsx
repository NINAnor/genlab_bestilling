import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import AsyncSelect from "react-select/async";

const datePortal = document.getElementById('date-portal');

export default function SelectCell({
  getValue,
  row: { original },
  column: { id },
  table,
  loadOptions,
  queryKey,
}) {
  const queryClient = useQueryClient();
  const initialValue = getValue();
  const [value, setValue] = useState(initialValue);

  // When the input is blurred, we'll call our table meta's updateData function
  const handleBlur = () => {
    if (value !== initialValue) {
      table.options.meta?.updateData({ id: original.id, [id]: value.id });
    }
  };

  // If the initialValue is changed external, sync it up with our state
  useEffect(() => {
    setValue(initialValue || "");
  }, [initialValue]);

  const load = async (input) => await queryClient.fetchQuery({ queryKey: [queryKey, input], queryFn: () => loadOptions(input) });

  return (
    <AsyncSelect
      defaultOptions
      loadOptions={load}
      getOptionLabel={(o) => o.name}
      getOptionValue={(o) => o.id}
      onBlur={handleBlur}
      classNamePrefix="react-select"
      className=""
      value={value}
      onChange={setValue}
      menuPortalTarget={datePortal}
    />
  );
}
