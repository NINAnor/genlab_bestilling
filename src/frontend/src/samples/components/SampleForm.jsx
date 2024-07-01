import { useForm } from "@tanstack/react-form";
import { Field as HUIField, Input, Button, Label } from "@headlessui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { client, config } from "../config";
import DatePicker from 'react-datepicker';

import "react-datepicker/dist/react-datepicker.css";

export default function SampleForm() {
  const queryClient = useQueryClient();

  const bulkCreate = useMutation({
    mutationFn: (value) => {
      return client.post("/api/samples/bulk/", {
        ...value,
        date: value.date.toLocaleDateString("en-US"),
        order: config.order,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["samples"] });
    },
  });

  const { handleSubmit, Field, Subscribe } = useForm({
    onSubmit: async ({ value, formApi }) => {
      try {
        await bulkCreate.mutateAsync(value);
        formApi.reset();
      } catch (e) {
        console.log(e);
      }
    },
    defaultValues: {
      quantity: 1,
      species: null,
      pop_id: null,
      date: null,
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        handleSubmit();
      }}
      className="flex gap-4 mb-5 items-end"
      id="add-rows"
    >
      <Field name="species">
        {({ state, handleChange, handleBlur }) => (
          <HUIField>
            <Label className="block">Species</Label>
            <input
              className="mt-1 block"
              value={state.value || ""}
              onChange={(e) => handleChange(e.target.value)}
              onBlur={handleBlur}
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
      <Field name="date">
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
          </HUIField>
        )}
      </Field>
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
            className="btn bg-primary"
            disabled={!canSubmit}
          >
            {isSubmitting ? <i className="fas fa-spin fa-spinner"></i> : "Add"}
          </Button>
        )}
      </Subscribe>
    </form>
  );
}
