// How the app words a criterion's proof and a spec's, with the numbers each comes from.
import type { CriterionProof, Proof, Report, SpecProof } from '@sulba/data/evidence';

const tests = (n: number) => (n === 1 ? '1 test' : `${n.toLocaleString()} tests`);

/** Why a criterion has its proof, such as "2 tests name it, and both passed". */
export function reasonOf(proof: CriterionProof): string {
  if (proof.state === 'failing') {
    return `${proof.failed} of the ${tests(proof.tests)} that name it failed`;
  }
  if (proof.state === 'proven') {
    return proof.tests === 1
      ? '1 test names it, and it passed'
      : `${tests(proof.tests)} name it, and all of them passed`;
  }
  if (proof.suspectSince !== null && proof.tests > 0) {
    return 'Reworded since its tests ran. Confirm they check the new wording to count them again';
  }
  if (proof.tests === 0) return 'No test in the latest runs names it';
  return `${proof.skipped} of the ${tests(proof.tests)} that name it skipped`;
}

/** A spec's proof in a few words, such as "2 of 3 proven" or "1 failing". */
export function specProofText(proof: SpecProof | undefined): string {
  if (!proof || proof.criteria === 0) return 'No criteria';
  if (proof.failing > 0) return `${proof.failing} failing`;
  return `${proof.proven} of ${proof.criteria} proven`;
}

/** The order the Evidence page lists criteria in: failing first, then unproven, then proven. */
export const proofOrder: Record<Proof, number> = { failing: 0, unproven: 1, proven: 2 };

/** A report's tests in a few words, such as "412 tests: 401 passed, 3 failed, 8 skipped". */
export function reportText(report: Report): string {
  return `${tests(report.tests)}: ${report.passed} passed, ${report.failed} failed, ${report.skipped} skipped`;
}

/** The run's page on GitHub. */
export function runUrl(repository: string, runId: number): string {
  return `https://github.com/${repository}/actions/runs/${runId}`;
}

/** The commit's page on GitHub. */
export function commitUrl(repository: string, sha: string): string {
  return `https://github.com/${repository}/commit/${sha}`;
}
