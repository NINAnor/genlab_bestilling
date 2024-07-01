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
    mutationFn: ({ value }) => {
      return client.post('/api/samples/bulk/', { ...value, order: config.order })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['samples']})
    }
  })

  const { handleSubmit, Field } = useForm({
    onSubmit: bulkCreate.mutate,
    defaultValues: {
      quantity: 1,
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
            <Input
              className="mt-1 block"
              defaultValue={state.value}
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
          <Input
            className="mt-1 block"
            defaultValue={state.value}
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
          <Input
            className="mt-1 block"
            defaultValue={state.value}
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
          <Input
            type="number"
            className="mt-1 block"
            defaultValue={state.value}
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
