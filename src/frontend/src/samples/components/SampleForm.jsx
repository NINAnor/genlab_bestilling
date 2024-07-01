import { useForm } from "@tanstack/react-form";
import {
  Field as HUIField,
  Input,
  Button,
  Label,
} from "@headlessui/react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { client, config } from '../config';

export default function SampleForm() {
  const queryClient = useQueryClient()

  const bulkCreate = useMutation({
    mutationFn: (value) => {
      return client.post('/api/samples/bulk/', { ...value, order: config.order })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['samples']})
    }
  })

  const { handleSubmit, Field } = useForm({
    onSubmit: async({ value, formApi })  => {
      try {
        await bulkCreate.mutateAsync(value)
        formApi.reset()
      } catch(e) {
        console.log(e);
      }
    },
    defaultValues: {
      quantity: 1,
      species: null,
      pop_id: null,
      date: null,
    }
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        handleSubmit();
      }}
      className="flex gap-4 mb-5 items-end"
    >
      <Field name="species">
        {({ state, handleChange, handleBlur }) => (
          <HUIField>
            <Label className="block">Species</Label>
            <input
              className="mt-1 block"
              value={state.value || ''}
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
            value={state.value || ''}
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
          <input
            className="mt-1 block"
            value={state.value || ''}
            onChange={(e) => handleChange(e.target.value)}
            onBlur={handleBlur}
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
      <Button type="submit" className="btn bg-primary">
        Add
      </Button>
    </form>
  );
}
