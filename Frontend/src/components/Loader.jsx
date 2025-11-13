import { PulseLoader } from 'react-spinners';

export default function Loader() {
  return (
    <div className="flex justify-center items-center py-8">
      <PulseLoader color="#f97316" size={12} />
    </div>
  );
}
