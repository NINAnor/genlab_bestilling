import {
  Button,
  Description,
  Dialog,
  DialogBackdrop,
  DialogPanel,
  DialogTitle,
  Textarea,
} from "@headlessui/react";
import { useState } from "react";

export default function PastableArrayInput({ state, handleChange }) {
  const [input, setInput] = useState('');
  let [isOpen, setIsOpen] = useState(false);

  const arrayFromInput = () => {
    const next = input.trim().split("\n");
    setInput("");
    handleChange(next);
    setIsOpen(false);
  };

  const open = () => {
    setInput(state.value.join('\n'));
    setIsOpen(true);
  }

  const invalid = input.indexOf("\t") > -1;

  return (
    <>
      <div className="max-h-28 overflow-auto">
        <ul className="list-disc text-sm">
          {state.value.map((o, i) => (
            <li key={`${i}-${o}`}>{o}</li>
          ))}
        </ul>
      </div>

      <div className="flex gap-2 mt-2">
        <Button className="btn bg-primary" onClick={open}>
          Paste from excel
        </Button>
        {state.value.length > 0 && (
          <Button
            className="btn bg-yellow-200"
            onClick={() => handleChange([])}
          >
            Clear
          </Button>
        )}
      </div>
      <Dialog
        open={isOpen}
        onClose={() => setIsOpen(false)}
        className="relative z-50"
      >
        <DialogBackdrop className="fixed inset-0 bg-black/30" />
        <div className="fixed inset-0 flex w-screen items-center justify-center p-4 ">
          <DialogPanel className="max-w-5xl bg-white py-5 px-5">
            <DialogTitle className="font-bold">Paste from excel</DialogTitle>
            <Description>
              Copy and Paste the column you want to insert, new lines are used
              as separator
            </Description>
            <Textarea
              className="border data-[hover]:shadow w-full my-2 max-h-96"
              value={input}
              rows={25}
              onChange={(e) => setInput(e.target.value)}
            ></Textarea>
            {invalid && (
              <div className="bg-red-400 p-2 rounded mb-3">
                It seems that you have pasted more than a single excel column,
                please check again
              </div>
            )}
            <div className="flex justify-start gap-4">
              <Button
                className="btn block bg-primary disabled:opacity-70"
                onClick={arrayFromInput}
                disabled={invalid || !input}
              >
                Insert {input.trim().split("\n").length || null}
              </Button>
              <Button
                className="btn block bg-yellow-200"
                onClick={() => setInput("")}
              >
                Clear
              </Button>
              <Button
                className="btn block bg-yellow-200 ml-auto"
                onClick={() => setIsOpen(false)}
              >
                Cancel
              </Button>
            </div>
          </DialogPanel>
        </div>
      </Dialog>
    </>
  );
}
