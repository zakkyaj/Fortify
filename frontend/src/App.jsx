/**
 * App — top-level shell.
 *
 * Renders the sidebar and the active page.
 * Step 1 only has Architecture.
 * Additional pages will be wired in as they are built.
 */
import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ArchitecturePage from './pages/ArchitecturePage'
import styles from './App.module.css'

const PAGES = {
  architecture: <ArchitecturePage />,
}

export default function App() {
  const [activePage, setActivePage] = useState('architecture')

  const currentPage = PAGES[activePage] ?? PAGES.architecture

  return (
    <div className={styles.shell}>
      <Sidebar activePage={activePage} onNavigate={setActivePage} />
      <main className={styles.main}>
        {currentPage}
      </main>
    </div>
  )
}
