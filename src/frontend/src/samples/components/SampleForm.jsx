import { useForm } from "@tanstack/react-form";
import { Button } from "@headlessui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { client, config } from "../config";
import AsyncSelect from "react-select/async";
import AsyncCreatableSelect from "react-select/async-creatable";
import { useStore } from "@tanstack/react-store";

import toast from "react-hot-toast";
import PastableArrayInput from "../../helpers/PastableArrayInput";
import { SELECT_STYLES } from "../../helpers/libs";

const speciesOptions = async (input) => {
  let base = `/api/species/?ext_order=${config.order}`;
  if (input) {
    base += `&name__icontains=${input}`;
  }
  return (await client.get(base)).data;
};

const sampleTypesOptions = async (input) => {
  return (
    await client.get(
      `/api/sample-types/?ext_order=${config.order}&name__icontains=${input}`
    )
  ).data;
};

const DEFAULT = {
  quantity: 1,
  species:
    config.analysis_data.species?.length === 1
      ? config.analysis_data.species[0]
      : null,
  pop_id: [],
  location: null,
  year: "",
  name: [],
  guid: [],
  type:
    config.analysis_data.sample_types?.length === 1
      ? config.analysis_data.sample_types[0]
      : null,
};

const HUIField = (props) => <div className="flex flex-col" {...props}></div>;
const Label = (props) => <label {...props}></label>;

export default function SampleForm() {
  const queryClient = useQueryClient();

  const bulkCreate = useMutation({
    mutationFn: (value) => {
      return client.post("/api/samples/bulk/", {
        ...value,
        species: value.species.id,
        type: value.type?.id,
        location: value.location?.id,
        order: config.order,
        quantity:
          value.quantity ||
          value.guid.length ||
          value.name.length ||
          value.pop_id.length,
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

  const { handleSubmit, Field, Subscribe, setFieldValue, store } = useForm({
    validators: {
      onChange({ value }) {
        const checks = {
          guid: value.guid.length,
          name: value.name.length,
          pop_id: value.pop_id.length,
        };

        if (Object.entries(checks).filter((c) => c[1]).length < 2)
          return undefined;

        const result = Object.values(checks)
          .filter((c) => c)
          .reduce((p, c) => {
            if (p !== c) {
              return -1;
            } else {
              return c;
            }
          });

        return result === -1
          ? `Pasted list fields must have the same number of items`
          : undefined;
      },
    },
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
    let base = `/api/locations/?ext_order=${config.order}&species=${species?.id}`;
    if (input) {
      base += `&name__icontains=${input}`;
    }
    return (await client.get(base)).data;
  };

  const formErrorMap = useStore(store, (state) => state.errorMap);

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
      {formErrorMap.onChange ? (
        <div className="mb-2 bg-red-300 p-2 rounded">
          <h4 className="text-xl font-bold capitalize">
            There was an error on the form
          </h4>
          {formErrorMap.onChange}
        </div>
      ) : null}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit();
        }}
        className=""
        id="add-rows"
      >
        <div className="flex gap-8 mb-4">
          {!config.analysis_data.needs_guid && (
            <Field name="guid">
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
          )}
          <Field name="name">
            {({ state, handleChange, handleBlur }) => (
              <HUIField>
                <Label
                  className="block"
                  title="physical identification marked on the sample"
                >
                  Sample Name - total: {state.value.length}{" "}
                  <i className="fas fa-circle-question"></i>
                </Label>
                <PastableArrayInput
                  state={state}
                  handleBlur={handleBlur}
                  handleChange={handleChange}
                />
              </HUIField>
            )}
          </Field>
          <Field name="pop_id">
            {({ state, handleChange, handleBlur }) => (
              <HUIField>
                <Label className="block">
                  Pop IDs - total: {state.value.length}
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
                  required
                  styles={SELECT_STYLES}
                />
              </HUIField>
            )}
          </Field>
          <Field name="type">
            {({ state, handleChange, handleBlur }) => (
              <HUIField>
                <Label className="block">Sample Type</Label>
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
                  required
                  styles={SELECT_STYLES}
                />
              </HUIField>
            )}
          </Field>

          <Field name="year">
            {({ state, handleChange, handleBlur }) => (
              <div className="flex flex-col">
                <Label className="block">Year</Label>
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  className="mt-1 block"
                  value={state.value}
                  onChange={(e) => handleChange(e.target.value)}
                  onBlur={handleBlur}
                  required
                />
              </div>
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
                      styles={SELECT_STYLES}
                    />
                  </HUIField>
                )}
              </Field>
            )}
          </Subscribe>
          <Subscribe
            selector={(state) =>
              state.values.name.length > 0 ||
              state.values.guid.length > 0 ||
              state.values.pop_id.length > 0
            }
          >
            {(hasPopulatedList) =>
              !hasPopulatedList && (
                <Field name="quantity">
                  {({ state, handleChange, handleBlur }) => (
                    <HUIField>
                      <Label className="block">Quantity</Label>
                      <input
                        type="text"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        className="mt-1 block"
                        value={state.value}
                        onChange={(e) => handleChange(e.target.value)}
                        onBlur={handleBlur}
                        required
                      />
                    </HUIField>
                  )}
                </Field>
              )
            }
          </Subscribe>
        </div>
        <div className="flex gap-8 mb-4 items-start">
          <Subscribe
            selector={(state) => [
              state.canSubmit,
              state.isSubmitting,
              state.values.quantity || 0,
              state.values.guid.length,
              state.values.name.length,
              state.values.pop_id.length,
            ]}
          >
            {([canSubmit, isSubmitting, ...rows]) => (
              <Button
                type="submit"
                className="btn bg-primary block"
                disabled={!canSubmit}
              >
                {isSubmitting ? (
                  <i className="fas fa-spin fa-spinner"></i>
                ) : (
                  `Add ${Math.max(...rows)} rows`
                )}
              </Button>
            )}
          </Subscribe>
        </div>
      </form>
    </>
  );
}
