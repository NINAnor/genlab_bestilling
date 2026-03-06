import { useEffect } from 'react';
import {
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast';
import ExtractionPlate from './components/ExtractionPlate';
import AnalysisPlate from './components/AnalysisPlate';
import usePlateStore from './store';
import { config } from './config';

const queryClient = new QueryClient()

function App() {
  const init = usePlateStore((s) => s.init);
  const plateType = usePlateStore((s) => s.plateType);

  useEffect(() => {
    init(config);
  }, [init]);

  return (
    <QueryClientProvider client={queryClient}>
      <Toaster />
      {plateType === 'extraction' && <ExtractionPlate />}
      {plateType === 'analysis' && <AnalysisPlate />}
      {!plateType && <p className="text-gray-500">Loading…</p>}
    </QueryClientProvider>
  )
}

export default App
