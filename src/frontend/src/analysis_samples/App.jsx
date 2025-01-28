import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import SearchApplyMarker from "./components/SearchApplyMarker";
import OrderMarker from "./components/OrderMarker";
const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex justify-between mb-5">
        <h2 className="text-4xl font-bold">Sample Selector</h2>

        <div className="mt-4 flex gap-8 justify-center">
          <a href="../../" className="btn bg-yellow-200">
            Back
          </a>
        </div>
      </div>
      <Toaster />
      <SearchApplyMarker />
      <h3 className="text-4xl font-bold pt-4 mb-4">Selected Samples</h3>
      <OrderMarker />
    </QueryClientProvider>
  );
}

export default App;
