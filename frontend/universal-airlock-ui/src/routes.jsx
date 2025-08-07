import { createBrowserRouter } from 'react-router-dom';
import Layout from './components/Layout.jsx';
import DashboardPage from './pages/DashboardPage.jsx';
import IdeationPage from './pages/IdeationPage.jsx';
import ValidationPage from './pages/ValidationPage.jsx';
import UploadPage from './pages/UploadPage.jsx';
import ReportsPage from './pages/ReportsPage.jsx';

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'ideation', element: <IdeationPage /> },
      { path: 'validation', element: <ValidationPage /> },
      { path: 'upload', element: <UploadPage /> },
      { path: 'reports', element: <ReportsPage /> }
    ]
  }
]);

export default router;
