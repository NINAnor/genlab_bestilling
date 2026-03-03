import { useEffect, useState } from 'react';
import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import useOrderStore from './store';
import { config } from './config';
import SampleMarkerTable from './components/SampleMarkerTable';
import FilterBar from './components/FilterBar';
import PlateSearch from './components/LoadPlate';
import SelectionActions from './components/SelectionActions';
import { useOrderSampleMarkers } from './hooks/useOrderSampleMarkers';

const queryClient = new QueryClient();

const INITIAL_FILTERS = {
  marker: '',
  species: '',
  sample_type: '',
  isolation_method: '',
  genlab_id: '',
  plate: '',
};

function OrderApp() {
  const init = useOrderStore((s) => s.init);
  const orderLabel = useOrderStore((s) => s.orderLabel);
  const sampleMarkers = useOrderStore((s) => s.sampleMarkers);

  const [filters, setFilters] = useState(INITIAL_FILTERS);

  useEffect(() => {
    init(config);
  }, [init]);

  // Fetch sample markers into the store with filters applied
  const { isLoading, isError } = useOrderSampleMarkers(filters);

  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
  };

  const handleResetFilters = () => {
    setFilters(INITIAL_FILTERS);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-4xl font-bold">
          {orderLabel ? `Analysis Order ${orderLabel}` : 'Sample Markers'}
        </h2>
        <a href="../" className="btn btn-sm btn-tertiary">
          <i className="fas fa-arrow-left mr-1"></i> Back
        </a>
      </div>

      <div className="space-y-4">
        <PlateSearch />

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-800">Sample Markers</h3>
            {Object.keys(sampleMarkers).length > 0 && (
              <span className="text-sm text-gray-500">
                {Object.keys(sampleMarkers).length} item(s)
              </span>
            )}
          </div>

          <FilterBar
            filters={filters}
            onFiltersChange={handleFiltersChange}
            onReset={handleResetFilters}
          />

          <SelectionActions />

          {isLoading && <p className="text-gray-400 mt-4">Loading…</p>}
          {isError && <p className="text-red-500 mt-4">Error loading sample markers</p>}
          {!isLoading && !isError && <SampleMarkerTable />}
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Toaster />
      <OrderApp />
    </QueryClientProvider>
  );
}

export default App;
