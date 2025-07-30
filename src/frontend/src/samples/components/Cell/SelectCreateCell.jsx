import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import AsyncSelect from "react-select/async-creatable";

const datePortal = document.getElementById("date-portal");

const CLASSNAMES = {
  container: () => "flex w-full",
  control: () => "px-4 w-full cursor-auto",
  menu: () => "bg-white border border-[#444] cursor-auto",
  option: () => "px-4 my-2 cursor-auto hover:bg-brand-primary",
  multiValue: () => "bg-brand-primary px-1 rounded cursor-auto",
};

export default function SelectCreateCell({
  getValue,
  row: { original },
  column: { id },
  table,
  loadOptions,
  queryKey,
  onCreate,
}) {
  const queryClient = useQueryClient();
  const initialValue = getValue();
  const [value, setValue] = useState(initialValue);
  const [key, setKey] = useState(0);

  // When the input is blurred, we'll call our table meta's updateData function
  const handleBlur = () => {
    if (value !== initialValue) {
      table.options.meta?.updateData({ id: original.id, [id]: value.id });
    }
  };

  const create = useMutation({
    mutationFn: onCreate,
    onSuccess: (data) => {
      setValue(data.data);
      queryClient.invalidateQueries({ queryKey: [queryKey] });
      setKey(key + 1);
    },
  });

  // If the initialValue is changed external, sync it up with our state
  useEffect(() => {
    setValue(initialValue || "");
  }, [initialValue]);

  const load = async (input) =>
    await queryClient.fetchQuery({
      queryKey: [queryKey, input],
      queryFn: () => loadOptions(input),
    });

  return (
    <AsyncSelect
      key={key}
      defaultOptions
      loadOptions={load}
      getOptionLabel={(o) => o.name}
      getOptionValue={(o) => o.id}
      onBlur={handleBlur}
      classNamePrefix="react-select"
      classNames={CLASSNAMES}
      value={value}
      onChange={setValue}
      menuPortalTarget={datePortal}
      unstyled
      getNewOptionData={(inputValue, optionLabel) => ({
        id: inputValue,
        name: optionLabel,
      })}
      onCreateOption={create.mutate}
    />
  );
}
