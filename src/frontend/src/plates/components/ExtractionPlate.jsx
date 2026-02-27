import PlateGrid from './PlateGrid';
import usePlateStore from '../store';

export default function ExtractionPlate() {
  const plateLabel = usePlateStore((s) => s.plateLabel);

  return (
    <div>
      <h2 className="text-4xl font-bold mb-5">Extraction Plate #{plateLabel}</h2>
      <div className="p-4 bg-white mb-2 rounded">
        <PlateGrid plateType="extraction" />
      </div>
    </div>
  );
}
