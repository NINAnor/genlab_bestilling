import { useForm } from "@tanstack/react-form";
import { HUIField, Label } from "../../helpers/components";
import AsyncSelect from "react-select/async";
import { Button } from "@headlessui/react";
import { client } from "../config";
import PastableArrayInput from "../../helpers/PastableArrayInput";

const speciesOptions = async (input) => {
  let base = `/api/species/?`;
  if (input) {
    base += `&name__icontains=${input}`;
  }
  return (await client.get(base)).data;
};

const sampleTypesOptions = async (input) => {
  return (await client.get(`/api/sample-types/?name__icontains=${input}`)).data;
};

const locationOptions = async (input) => {
  let base = `/api/locations/`;
  if (input) {
    base += `?name__icontains=${input}`;
  }
  return (await client.get(base)).data;
};

function prevent(e) {
  e.preventDefault();
  e.stopPropagation();
}

export default function Filters({ onSearch }) {
  const { handleSubmit, Field, Subscribe } = useForm({
    onSubmit: ({ value, formApi }) => {
      let o = Object.fromEntries(
        Object.entries(value).filter(([_, v]) => v != null)
      );
      if (Object.keys(o)) {
        onSearch(new URLSearchParams(o).toString());
      }
    },
    defaultValues: {
      order: null,
      species: null,
      year: null,
      type: null,
      name__startswith: null,
      genlab_id__startswith: null,
      guid__in: []
    },
  });

  const emulateEnter = (e) => {
    if (e.key === "Enter" || e.keyCode === 13) {
      prevent(e)
      handleSubmit();
    }
  };

  return (
    <div>
      <div className="flex flex-wrap gap-4">
        <div className="flex mb-4">
          <Field name="order">
            {({ state, handleChange, handleBlur }) => (
              <HUIField>
                <Label className="block">Order ID</Label>
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  className="mt-1 block"
                  value={state.value}
                  onChange={(e) => handleChange(e.target.value)}
                  onBlur={handleBlur}
                  onKeyUp={emulateEnter}
                  onSubmit={prevent}
                />
              </HUIField>
            )}
          </Field>
        </div>
        <div className="flex gap-8 mb-4">
          <Field name="guid__in">
            {({ state, handleChange, handleBlur }) => (
              <HUIField>
                <Label className="block">
                  Guid - total: {state.value.length}
                </Label>
                <PastableArrayInput
                  state={state}
                  handleBlur={handleBlur}
                  handleChange={handleChange}
                />
              </HUIField>
            )}
          </Field>
        </div>
        <div className="flex gap-8 mb-4">
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
        </div>
        <div className="flex gap-8 mb-4">
          <Field name="type">
            {({ state, handleChange, handleBlur }) => (
              <HUIField>
                <Label className="block">Sample type</Label>
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
        </div>
        <div className="flex gap-8 mb-4">
          <Field name="year">
            {({ state, handleChange, handleBlur }) => (
              <HUIField>
                <Label className="block">Year</Label>
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  className="mt-1 block"
                  value={state.value}
                  onChange={(e) => handleChange(e.target.value)}
                  onBlur={handleBlur}
                  onKeyUp={emulateEnter}
                  onSubmit={prevent}
                />
              </HUIField>
            )}
          </Field>
        </div>
        <div className="flex gap-8 mb-4">
          <Field name="name__istartswith">
            {({ state, handleChange, handleBlur }) => (
              <HUIField>
                <Label className="block">Sample name</Label>
                <input
                  type="text"
                  className="mt-1 block"
                  value={state.value}
                  onChange={(e) => handleChange(e.target.value)}
                  onBlur={handleBlur}
                  onKeyUp={emulateEnter}
                  onSubmit={prevent}
                />
              </HUIField>
            )}
          </Field>
        </div>
        <div className="flex gap-8 mb-4">
          <Field name="genlab_id__istartswith">
            {({ state, handleChange, handleBlur }) => (
              <HUIField>
                <Label className="block">Genlab ID</Label>
                <input
                  type="text"
                  className="mt-1 block"
                  value={state.value}
                  onChange={(e) => handleChange(e.target.value)}
                  onBlur={handleBlur}
                  onKeyUp={emulateEnter}
                  onSubmit={prevent}
                />
              </HUIField>
            )}
          </Field>
        </div>
        <div className="flex gap-8 mb-4">
          <Field name="location">
            {({ state, handleChange, handleBlur }) => (
              <HUIField>
                <Label className="block">Location</Label>
                <AsyncSelect
                  defaultOptions
                  loadOptions={locationOptions}
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
        </div>
      </div>

      <div className="flex gap-8 mb-4 items-center justify-center">
        <Subscribe selector={(state) => [state.canSubmit, state.isSubmitting]}>
          {([canSubmit, isSubmitting]) => (
            <Button
              className="btn bg-primary block disabled:opacity-50"
              disabled={!canSubmit}
              onClick={handleSubmit}
            >
              {isSubmitting ? (
                <i className="fas fa-spin fa-spinner"></i>
              ) : (
                `Search`
              )}
            </Button>
          )}
        </Subscribe>
      </div>
    </div>
  );
}
