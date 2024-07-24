import { useForm } from "@tanstack/react-form";
import { Field as HUIField, Button, Label } from "@headlessui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { client, config } from "../config";
import DatePicker from "react-datepicker";
import AsyncSelect from "react-select/async";
import AsyncCreatableSelect from "react-select/async-creatable";

import "react-datepicker/dist/react-datepicker.css";
import toast from "react-hot-toast";

const speciesOptions = async (input) => {
  let base = `/api/species/?order=${config.order}`;
  if (input) {
    base += `&name__icontains=${input}`;
  }
  return (await client.get(base)).data;
};

const sampleTypesOptions = async (input) => {
  return (
    await client.get(
      `/api/sample-types/?order=${config.order}&name__icontains=${input}`
    )
  ).data;
};

const DEFAULT = {
  quantity: 1,
  species:
    config.analysis_data.species?.length === 1
      ? config.analysis_data.species[0]
      : null,
  pop_id: null,
  date: null,
  location: null,
  type:
    config.analysis_data.sample_types?.length === 1
      ? config.analysis_data.sample_types[0]
      : null,
};

const FieldErrors = ({ state }) => {state.meta.errors.length > 0 && (
  <div className="bg-red-400 p-2 text-sm mt-2">
    {state.meta.errors.map((err) => (
      <div key={err}>{err}</div>
    ))}
  </div>
)}

export default function SampleForm() {
  const queryClient = useQueryClient();

  const bulkCreate = useMutation({
    mutationFn: (value) => {
      return client.post("/api/samples/bulk/", {
        ...value,
        date: value.date ? value.date.toLocaleDateString("en-US") : null,
        species: value.species.id,
        type: value.type?.id,
        location: value.location?.id,
        order: config.order,
      });
    },
    onSuccess: () => {
      toast.success("Samples created!");
      queryClient.invalidateQueries({ queryKey: ["samples"] });
    },
    onError: () => {
      toast.error("There was an error!");
    },
  });

  const { handleSubmit, Field, Subscribe, setFieldValue } = useForm({
    onSubmit: async ({ value, formApi }) => {
      try {
        await bulkCreate.mutateAsync(value);
        formApi.reset();
      } catch (e) {
        // console.log(e);
      }
    },
    defaultValues: DEFAULT,
  });

  const createLocation = useMutation({
    mutationFn: (value) => {
      return client.post("/api/locations/", {
        name: value,
      });
    },
    onSuccess: (data) => {
      setFieldValue("location", data.data);
    },
  });

  const locationOptions = async (input, species) => {
    let base = `/api/locations/?order=${config.order}&species=${species?.id}`;
    if (input) {
      base += `&name__icontains=${input}`;
    }
    return (await client.get(base)).data;
  };

  return (
    <>
      {bulkCreate.error && (
        <div className="mb-2 bg-red-300 p-2 rounded">
          <h4 className="text-xl font-bold capitalize">
            {bulkCreate.error.response.data.type.replace("_", " ")}
          </h4>
          <ul className="list-disc px-5">
            {bulkCreate.error.response.data.errors.map((e) => (
              <li key={e.attr + e.code}>
                {e.attr} - {e.detail}
              </li>
            ))}
          </ul>
        </div>
      )}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit();
        }}
        className="flex gap-4 mb-5 items-start flex-wrap"
        id="add-rows"
      >
        <Field name="species">
          {({ state, handleChange, handleBlur }) => (
            <HUIField>
              <Label className="block">Species</Label>
              <AsyncSelect
                defaultOptions
                loadOptions={speciesOptions}
                getOptionLabel={(o) => o.name}
                getOptionValue={(o) => o.id}
                onBlur={handleBlur}
                classNamePrefix="react-select"
                className=""
                value={state.value}
                onChange={handleChange}
              />
            </HUIField>
          )}
        </Field>
        <Field name="type">
          {({ state, handleChange, handleBlur }) => (
            <HUIField>
              <Label className="block">Type</Label>
              <AsyncSelect
                defaultOptions
                loadOptions={sampleTypesOptions}
                getOptionLabel={(o) => o.name}
                getOptionValue={(o) => o.id}
                onBlur={handleBlur}
                classNamePrefix="react-select"
                className=""
                value={state.value}
                onChange={handleChange}
              />
            </HUIField>
          )}
        </Field>
        <Field name="pop_id">
          {({ state, handleChange, handleBlur }) => (
            <HUIField>
              <Label className="block">Pop ID</Label>
              <input
                className="mt-1 block"
                value={state.value || ""}
                onChange={(e) => handleChange(e.target.value)}
                onBlur={handleBlur}
              />
            </HUIField>
          )}
        </Field>
        <Field
          name="date"
          validators={{
            onChange: ({ value }) => (!value ? "A date is required" : null),
          }}
        >
          {({ state, handleChange, handleBlur }) => (
            <HUIField>
              <Label className="block">Date</Label>
              <DatePicker
                showIcon
                className="mt-1 block"
                selected={state.value}
                onChange={(e) => handleChange(e)}
                onBlur={handleBlur}
                dateFormat="dd/MM/YYYY"
              />
              <FieldErrors state={state} />
            </HUIField>
          )}
        </Field>
        <Subscribe selector={(state) => state.values.species}>
          {(species) => (
            <Field name="location">
              {({ state, handleChange, handleBlur }) => (
                <HUIField>
                  <Label className="block">Location</Label>
                  <AsyncCreatableSelect
                    defaultOptions
                    isClearable
                    isDisabled={!species}
                    loadOptions={(input) => locationOptions(input, species)}
                    getOptionLabel={(o) => o.name}
                    getOptionValue={(o) => o.id}
                    getNewOptionData={(inputValue, optionLabel) => ({
                      id: inputValue,
                      name: optionLabel,
                    })}
                    onBlur={handleBlur}
                    classNamePrefix="react-select"
                    className=""
                    value={state.value}
                    onChange={handleChange}
                    onCreateOption={createLocation.mutate}
                  />
                </HUIField>
              )}
            </Field>
          )}
        </Subscribe>
        <Field name="quantity">
          {({ state, handleChange, handleBlur }) => (
            <HUIField>
              <Label className="block">Quantity</Label>
              <input
                type="number"
                className="mt-1 block"
                value={state.value}
                onChange={(e) => handleChange(e.target.value)}
                onBlur={handleBlur}
              />
            </HUIField>
          )}
        </Field>
        <Subscribe selector={(state) => [state.canSubmit, state.isSubmitting]}>
          {([canSubmit, isSubmitting]) => (
            <Button
              type="submit"
              className="btn bg-primary self-start"
              disabled={!canSubmit}
            >
              {isSubmitting ? (
                <i className="fas fa-spin fa-spinner"></i>
              ) : (
                "Add"
              )}
            </Button>
          )}
        </Subscribe>
      </form>
    </>
  );
}
