/**
 * App — top-level shell.
 *
 * Wraps everything in ExperimentProvider so all pages share experiment state.
 * Sidebar unlocks "Attack & Run" once an architecture has been registered.
 */
import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ArchitecturePage from './pages/ArchitecturePage'
import ExperimentPage from './pages/ExperimentPage'
import { ExperimentProvider, useExperiment } from './store/experimentStore'
import styles from './App.module.css'

function Shell() {
  const [activePage, setActivePage] = useState('architecture')
  const { architectureId } = useExperiment()

  // Unlock experiment page only once an architecture has been registered
  const unlockedSteps = new Set(['architecture'])
  if (architectureId) unlockedSteps.add('experiment')

  const pages = {
    architecture: <ArchitecturePage />,
    experiment:   <ExperimentPage />,
  }

  return (
    <div className={styles.shell}>
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
        unlockedSteps={unlockedSteps}
      />
      <main className={styles.main}>
        {pages[activePage] ?? pages.architecture}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <ExperimentProvider>
      <Shell />
    </ExperimentProvider>
  )
}
