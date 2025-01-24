import { HUIField, Label } from "../../helpers/components";
import { Button } from "@headlessui/react";
import { useForm } from "@tanstack/react-form";
import Table from "./SampleTable";
import { client, config } from "../config";
import AsyncSelect from "react-select/async";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import toast from "react-hot-toast";

const markersOptions = async (input) => {
  return (
    await client.get(
      `/api/markers/?analysis_order=${config.order}&name__istartswith=${input}`
    )
  ).data;
};

export default function SearchApplyMarker() {
  const queryClient = useQueryClient()
;
  const bulkCreate = useMutation({
    mutationFn: (value) => {
      return client.post("/api/sample-marker-analysis/bulk/", {
        samples: Object.entries(value.selectedSamples).filter(([_k, value]) => value).map(([key, _v]) => key),
        markers: value.markers.map(m => m.name),
        order: config.order,
      });
    },
    onSuccess: () => {
      toast.success("Samples added!");
      queryClient.invalidateQueries({ queryKey: ["sample-marker-analysis"] });
    },
    onError: () => {
      toast.error("There was an error!");
    },
  });

  const { handleSubmit, Field, Subscribe } = useForm({
    onSubmit: async ({ value }) => {
      try {
        await bulkCreate.mutateAsync(value);
      } catch (e) {
        console.log(e);
        toast.error("There was an error!");
      }
    },
    defaultValues: {
      selectedSamples: {},
      markers: [],
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        handleSubmit();
      }}
      id="add-rows"
    >
      <div className="flex gap-8 items-end">
        <Field name="markers">
          {({ state, handleChange, handleBlur }) => (
            <HUIField>
              <Label id="markers-label" className="block">Markers</Label>
              <AsyncSelect
                isMulti
                defaultOptions
                loadOptions={markersOptions}
                getOptionLabel={(o) => o.name}
                getOptionValue={(o) => o.name}
                onBlur={handleBlur}
                classNamePrefix="react-select"
                className=""
                value={state.value}
                onChange={handleChange}
                required
              />
            </HUIField>
          )}
        </Field>
        <Subscribe
          selector={(state) => [
            state.canSubmit,
            state.isSubmitting,
            state.values.selectedSamples,
            state.values.markers,
          ]}
        >
          {([canSubmit, isSubmitting, samples, markers]) => (
            <Button
              onClick={handleSubmit}
              className="btn bg-primary block disabled:opacity-50"
              disabled={!canSubmit || !Object.values(samples).some(_ => _) || !markers.length}
            >
              {isSubmitting ? (
                <i className="fas fa-spin fa-spinner"></i>
              ) : (
                `Add`
              )}
            </Button>
          )}
        </Subscribe>
      </div>
      <div className="flex my-4">
        <Subscribe
            selector={(state) => [
              state.values.markers,
            ]}
          >
            {([markers]) => (
          <Field name="selectedSamples">
            {({ state, handleChange }) => (
              <HUIField>
                <Label className="block">
                  Selected Samples - total: {Object.values(state.value).filter(_ => _).length}
                </Label>
                <Table rowSelection={state.value} setRowSelection={handleChange} markers={markers} />
              </HUIField>
            )}
          </Field>
            )}
        </Subscribe>
      </div>
    </form>
  );
}
