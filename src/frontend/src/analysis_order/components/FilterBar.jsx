import { useState, useCallback, useEffect } from 'react';
import PropTypes from 'prop-types';
import AsyncSelect from 'react-select/async';
import {
  searchAnalysisOrders,
  useMarkerFilterOptions,
  useSpeciesFilterOptions,
  useSampleTypeFilterOptions,
  useIsolationMethodFilterOptions,
} from '../hooks/useFilterOptions';
import useOrderStore from '../store';

/**
 * Filter bar for sample markers list.
 * Allows filtering by analysis order, marker, species, sample type, isolation method, and genlab_id.
 */
export default function FilterBar({ filters, onFiltersChange, onReset }) {
  const orderId = useOrderStore((s) => s.orderId);
  const orderLabel = useOrderStore((s) => s.orderLabel);
  const setSelectedOrder = useOrderStore((s) => s.setSelectedOrder);

  // Track the selected order option for react-select
  const [selectedOrderOption, setSelectedOrderOption] = useState(null);

  // Sync selected order option when orderId/orderLabel changes
  useEffect(() => {
    if (orderId && orderLabel) {
      setSelectedOrderOption({ value: orderId, label: orderLabel });
    } else {
      setSelectedOrderOption(null);
    }
  }, [orderId, orderLabel]);

  const { data: markers = [], isLoading: markersLoading } = useMarkerFilterOptions();
  const { data: species = [], isLoading: speciesLoading } = useSpeciesFilterOptions();
  const { data: sampleTypes = [], isLoading: typesLoading } = useSampleTypeFilterOptions();
  const { data: isolationMethods = [], isLoading: methodsLoading } =
    useIsolationMethodFilterOptions();

  const updateFilter = (key, value) => {
    onFiltersChange({ ...filters, [key]: value || '' });
  };

  // Load options for async select
  const loadOrderOptions = useCallback(async (inputValue) => {
    return searchAnalysisOrders(inputValue);
  }, []);

  const handleOrderChange = (option) => {
    if (option) {
      setSelectedOrder(option.value, option.label);
      setSelectedOrderOption(option);
    } else {
      setSelectedOrder(null, null);
      setSelectedOrderOption(null);
    }
  };

  const handleReset = () => {
    setSelectedOrder(null, null);
    setSelectedOrderOption(null);
    onReset();
  };

  const hasActiveFilters = orderId || Object.values(filters).some((v) => v !== '');

  // Custom styles for react-select to match other inputs
  const selectStyles = {
    control: (base) => ({
      ...base,
      minHeight: '34px',
      fontSize: '0.875rem',
    }),
    valueContainer: (base) => ({
      ...base,
      padding: '0 8px',
    }),
    input: (base) => ({
      ...base,
      margin: 0,
      padding: 0,
    }),
    indicatorsContainer: (base) => ({
      ...base,
      height: '32px',
    }),
    menu: (base) => ({
      ...base,
      fontSize: '0.875rem',
      zIndex: 50,
    }),
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-700">Filters</h3>
        {hasActiveFilters && (
          <button
            type="button"
            onClick={handleReset}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            Clear all
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-3">
        {/* Analysis Order filter - searchable async select */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Analysis Order</label>
          <AsyncSelect
            value={selectedOrderOption}
            onChange={handleOrderChange}
            loadOptions={loadOrderOptions}
            defaultOptions
            cacheOptions
            isClearable
            placeholder="Search orders..."
            noOptionsMessage={() => 'Type to search orders'}
            styles={selectStyles}
            classNamePrefix="react-select"
          />
        </div>

        {/* Marker filter */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Marker</label>
          <select
            value={filters.marker || ''}
            onChange={(e) => updateFilter('marker', e.target.value)}
            disabled={markersLoading}
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All markers</option>
            {markers.map((m, idx) => (
              <option key={m.name ?? `marker-${idx}`} value={m.name}>
                {m.name}
              </option>
            ))}
          </select>
        </div>

        {/* Species filter */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Species</label>
          <select
            value={filters.species || ''}
            onChange={(e) => updateFilter('species', e.target.value)}
            disabled={speciesLoading}
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All species</option>
            {species.map((s, idx) => (
              <option key={s.id ?? `species-${idx}`} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        {/* Sample Type filter */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Sample Type</label>
          <select
            value={filters.sample_type || ''}
            onChange={(e) => updateFilter('sample_type', e.target.value)}
            disabled={typesLoading}
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All types</option>
            {sampleTypes.map((t, idx) => (
              <option key={t.id ?? `type-${idx}`} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        {/* Isolation Method filter */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Isolation Method
          </label>
          <select
            value={filters.isolation_method || ''}
            onChange={(e) => updateFilter('isolation_method', e.target.value)}
            disabled={methodsLoading}
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All methods</option>
            {isolationMethods.map((m, idx) => (
              <option key={m.id ?? `method-${idx}`} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </div>

        {/* Genlab ID search */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Genlab ID</label>
          <input
            type="text"
            value={filters.genlab_id || ''}
            onChange={(e) => updateFilter('genlab_id', e.target.value)}
            placeholder="Search by ID…"
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Plate search */}
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Extraction Plate</label>
          <input
            type="text"
            value={filters.plate || ''}
            onChange={(e) => updateFilter('plate', e.target.value)}
            placeholder="Search plate…"
            className="w-full border border-gray-300 rounded px-2 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>
    </div>
  );
}

FilterBar.propTypes = {
  filters: PropTypes.shape({
    marker: PropTypes.string,
    species: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    sample_type: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    isolation_method: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    genlab_id: PropTypes.string,
    plate: PropTypes.string,
  }).isRequired,
  onFiltersChange: PropTypes.func.isRequired,
  onReset: PropTypes.func.isRequired,
};
