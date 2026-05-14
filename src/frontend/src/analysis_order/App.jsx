import { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import useOrderStore from './store';
import { config } from './config';
import SampleMarkerTable from './components/SampleMarkerTable';
import FilterBar from './components/FilterBar';
import PlateSearch from './components/LoadPlate';
import SelectionActions from './components/SelectionActions';
import { useOrderSampleMarkers } from './hooks/useOrderSampleMarkers';
import { useCompleteOrder } from './hooks/useCompleteOrder';
import { useSetOrderInProgress } from './hooks/useSetOrderInProgress';

const queryClient = new QueryClient();

const INITIAL_FILTERS = {
  marker: '',
  species: '',
  sample_type: '',
  isolation_method: '',
  genlab_id: '',
  plate: '',
  status: '',
};

function OrderApp() {
  const init = useOrderStore((s) => s.init);
  const orderId = useOrderStore((s) => s.orderId);
  const orderLabel = useOrderStore((s) => s.orderLabel);
  const orderStatus = useOrderStore((s) => s.orderStatus);
  const orderStatusLabel = useOrderStore((s) => s.orderStatusLabel);
  const sampleMarkers = useOrderStore((s) => s.sampleMarkers);
  const showFishId = useOrderStore((s) => s.showFishId);
  const toggleShowFishId = useOrderStore((s) => s.toggleShowFishId);

  const [filters, setFilters] = useState(INITIAL_FILTERS);

  const { mutate: completeOrder, isPending: isCompleting } = useCompleteOrder({
    onSuccess: () => {
      // Redirect to the analysis order detail page
      window.location.href = `/staff/orders/analysis/${orderId}/`;
    },
  });
  const { mutate: setOrderInProgress, isPending: isSettingInProgress } = useSetOrderInProgress({
    onSuccess: () => {
      // Redirect to the analysis order detail page
      window.location.href = `/staff/orders/analysis/${orderId}/`;
    },
  });

  useEffect(() => {
    init(config);
  }, [init]);

  // Fetch sample markers into the store with filters applied
  const { isLoading, isError, fetchNextPage, hasNextPage, isFetchingNextPage, data } =
    useOrderSampleMarkers(filters);

  const totalCount = data?.pages?.[0]?.count;

  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
  };

  const handleResetFilters = () => {
    setFilters(INITIAL_FILTERS);
  };

  const handleCompleteOrder = () => {
    if (!orderId) return;
    if (window.confirm(`Are you sure you want to mark this order as completed?`)) {
      completeOrder(orderId);
    }
  };

  const handleSetInProgress = () => {
    if (!orderId) return;
    if (window.confirm(`Are you sure you want to mark this order as in progress?`)) {
      setOrderInProgress(orderId);
    }
  };

  const statusTagClass =
    {
      draft: 'bg-gray-100 text-gray-700 border-gray-200',
      confirmed: 'bg-blue-100 text-blue-700 border-blue-200',
      processing: 'bg-amber-100 text-amber-700 border-amber-200',
      completed: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    }[orderStatus] || 'bg-gray-100 text-gray-700 border-gray-200';

  return (
    <div>
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <h2 className="text-4xl font-bold">
            {orderLabel ? `Analysis Order ${orderLabel}` : 'Sample Markers'}
          </h2>
          {orderId && orderStatusLabel && (
            <span
              className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${statusTagClass}`}
            >
              {orderStatusLabel}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {orderId && (
            <>
              <button
                type="button"
                onClick={handleSetInProgress}
                disabled={isSettingInProgress || isCompleting}
                className="btn btn-sm btn-secondary"
              >
                {isSettingInProgress ? (
                  <>
                    <i className="fas fa-spinner fa-spin mr-1"></i> Updating...
                  </>
                ) : (
                  <>
                    <i className="fas fa-play mr-1"></i> Mark as In Progress
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={handleCompleteOrder}
                disabled={isCompleting || isSettingInProgress}
                className="btn btn-sm btn-primary"
              >
                {isCompleting ? (
                  <>
                    <i className="fas fa-spinner fa-spin mr-1"></i> Completing...
                  </>
                ) : (
                  <>
                    <i className="fas fa-check mr-1"></i> Mark as Completed
                  </>
                )}
              </button>
            </>
          )}
          <a href="../" className="btn btn-sm btn-tertiary">
            <i className="fas fa-arrow-left mr-1"></i> Back
          </a>
        </div>
      </div>

      <div className="space-y-4">
        <PlateSearch />

        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-800">Sample Markers</h3>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showFishId}
                  onChange={toggleShowFishId}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                Show Fish ID
              </label>
              {Object.keys(sampleMarkers).length > 0 && (
                <span className="text-sm text-gray-500">
                  {Object.keys(sampleMarkers).length}
                  {totalCount ? ` / ${totalCount}` : ''} item(s)
                </span>
              )}
            </div>
          </div>

          <FilterBar
            filters={filters}
            onFiltersChange={handleFiltersChange}
            onReset={handleResetFilters}
          />

          <SelectionActions />

          {isLoading && <p className="text-gray-400 mt-4">Loading…</p>}
          {isError && <p className="text-red-500 mt-4">Error loading sample markers</p>}
          {!isLoading && !isError && (
            <SampleMarkerTable
              fetchNextPage={fetchNextPage}
              hasNextPage={hasNextPage}
              isFetchingNextPage={isFetchingNextPage}
              totalCount={totalCount}
            />
          )}
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
