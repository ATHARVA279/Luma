import { PulseLoader } from 'react-spinners';

export default function Loader() {
  return (
    <div className="flex justify-center items-center p-4">
      <PulseLoader color="#8b5cf6" size={12} />
    </div>
  );
}
