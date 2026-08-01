import { UploadForm } from "./UploadForm";

export default function UploadPage() {
  return <div className="page upload-page"><header className="page-header"><p className="eyebrow">Add training footage</p><h1>Upload once. <span>Find it later.</span></h1><p className="header-copy">Source video goes directly to Backblaze B2. Temporary processing files are removed after indexing.</p></header><UploadForm /></div>;
}

