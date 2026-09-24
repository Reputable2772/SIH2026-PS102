import React, { useState } from 'react';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import { Navbar } from './components/layout/Navbar';
import { Sidebar, NavTab } from './components/layout/Sidebar';
import { DossierModal } from './components/dossier/DossierModal';
import { OverviewPage } from './pages/OverviewPage';
import { MapPage } from './pages/MapPage';
import { DetectorsPage } from './pages/DetectorsPage';
import { WorksPage } from './pages/WorksPage';
import { EntitiesPage } from './pages/EntitiesPage';
import { CitizenPage } from './pages/CitizenPage';
import { ValidationPage } from './pages/ValidationPage';

export function AppContent() {
  const [activeTab, setActiveTab] = useState<NavTab>('overview');
  const [activeDossierId, setActiveDossierId] = useState<string | null>(null);
  const [worksFilter, setWorksFilter] = useState<{
    priority?: string;
    category?: string;
    query?: string;
    state?: string;
  } | null>(null);

  const handleOpenDossier = (recId: string) => {
    setActiveDossierId(recId);
  };

  const handleCloseDossier = () => {
    setActiveDossierId(null);
  };

  const handleNavigateToWorks = (filter?: {
    priority?: string;
    category?: string;
    query?: string;
    state?: string;
  }) => {
    setWorksFilter(filter || null);
    setActiveTab('works');
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden mesh-bg">
      {/* Top Navbar with Dynamic Persona Switcher */}
      <Navbar onNavigateToWorks={handleNavigateToWorks} />

      {/* Main Content Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

        {/* Dynamic View Body */}
        <main className="flex-1 flex flex-col overflow-hidden bg-[#0F172A]/40 backdrop-blur-sm">
          {activeTab === 'overview' && (
            <OverviewPage
              onOpenDossier={handleOpenDossier}
              onNavigateToWorks={handleNavigateToWorks}
            />
          )}
          {activeTab === 'map' && <MapPage onOpenDossier={handleOpenDossier} />}
          {activeTab === 'detectors' && <DetectorsPage />}
          {activeTab === 'works' && (
            <WorksPage
              onOpenDossier={handleOpenDossier}
              initialFilter={worksFilter}
            />
          )}
          {activeTab === 'entities' && <EntitiesPage onOpenDossier={handleOpenDossier} />}
          {activeTab === 'citizen' && <CitizenPage onOpenDossier={handleOpenDossier} />}
          {activeTab === 'validation' && <ValidationPage />}
        </main>
      </div>

      {/* Explainable 5-Question Governance Dossier Modal */}
      {activeDossierId && (
        <DossierModal workRecId={activeDossierId} onClose={handleCloseDossier} />
      )}
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <AppContent />
      </ToastProvider>
    </AuthProvider>
  );
}
