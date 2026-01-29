import { FilePlus, Play, Trash2 } from "lucide-react";

function ProcessTextPage() {
  return (
    <div className="h-full flex flex-col">
      <h1 className="px-8">Input Text</h1>
      <hr className="w-full border-t border-gray-300 mt-4" />
      <div className="flex-1 m-8 flex flex-col justify-center items-center rounded-lg bg-(--grayish)">
        <textarea className="w-full h-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent" placeholder="Enter your message here..."></textarea>
      </div>
      <hr className="w-full border-t border-gray-300 mt-4" />
      <div className="w-full px-8 py-4 flex justify-center sm:justify-start gap-4">
        <button className="flex items-center gap-2 px-4 py-2 rounded-lg
    bg-black text-white
    hover:bg-neutral-600 active:bg-neutral-600 focus-visible:outline-offset-2 focus-visible:outline-black">
          <Play className="w-5 h-5" />
          <span>Run</span>
        </button>
        <button className="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-400 text-slate-700 hover:bg-slate-100 hover:border-slate-500 active:bg-slate-200 focus-visible:outline-offset-2 focus-visible:outline-slate-500">
          <Trash2 className="w-5 h-5" />
          <span>Clear</span>
        </button>
      </div>

    </div>
  );
}

export default ProcessTextPage;
