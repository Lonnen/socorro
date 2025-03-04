# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from socorro.processor.rules.base import Rule


# Kinds of memory reporters.
KIND_NONHEAP = 0
KIND_HEAP = 1
# Type of units used by memory reporters.
UNITS_BYTES = 0
# For more information on those values, see:
# https://dxr.mozilla.org/mozilla-central/source/xpcom/base/nsIMemoryReporter.idl#27-125


class MemoryReportExtraction(Rule):
    """Extract key measurements from the memory_report object into a more
    comprehensible and usable dictionary.

    """

    def predicate(self, raw_crash, dumps, processed_crash, proc_meta):
        try:
            # Verify that...
            return (
                # ... we have a pid...
                "pid" in processed_crash["json_dump"]
                # ... we have a memory report...
                and bool(processed_crash["memory_report"])
                # ... and that memory report is recognisable.
                and "version" in processed_crash["memory_report"]
                and "reports" in processed_crash["memory_report"]
                and "hasMozMallocUsableSize" in processed_crash["memory_report"]
            )
        except KeyError:
            return False

    def action(self, raw_crash, dumps, processed_crash, processor_meta):
        pid = processed_crash["json_dump"]["pid"]
        memory_report = processed_crash["memory_report"]

        try:
            measures = self._get_memory_measures(memory_report, pid)
        except ValueError as e:
            self.logger.info(f"Unable to extract measurements from memory report: {e}")
            return
        except KeyError as e:
            self.logger.info(
                "Unable to extract measurements from memory report: "
                "key {} is missing from a report".format(e)
            )
            return

        processed_crash["memory_measures"] = measures

    def _get_memory_measures(self, memory_report, pid):
        explicit_heap = 0
        explicit_nonheap = 0
        pid_found = False
        pid_str = f"(pid {pid})"

        # These ones are in the memory report.
        # Note: theses keys use dashes instead of underscores because that's
        # how they appear in the paths of the memory report. For the sake of
        # consistent naming in our documents, we will rewrite them before
        # adding them to the processed_crash.
        metrics_measured = {
            "gfx-textures": 0,
            "ghost-windows": 0,
            "heap-allocated": 0,
            "host-object-urls": 0,
            "private": 0,
            "resident": 0,
            "resident-unique": 0,
            "system-heap-allocated": 0,
            "vsize-max-contiguous": 0,
            "vsize": 0,
        }

        # These ones are derived from the memory report.
        metrics_derived = {
            "explicit": 0,
            "heap-overhead": 0,
            "heap-unclassified": 0,
            "images": 0,
            "js-main-runtime": 0,
            "top-none-detached": 0,
        }

        all_metrics = {}
        all_metrics.update(metrics_measured)
        all_metrics.update(metrics_derived)

        # Process reports
        for report in memory_report["reports"]:
            process = report["process"]

            if pid_str not in process:
                continue

            pid_found = True

            path = report["path"]
            kind = report["kind"]
            units = report["units"]
            amount = report["amount"]

            if path.startswith("explicit/"):
                if units != UNITS_BYTES:
                    raise ValueError(
                        "bad units for an explicit/ report: {}, {}".format(
                            path, str(units)
                        )
                    )

                if kind == KIND_NONHEAP:
                    explicit_nonheap += amount
                elif kind == KIND_HEAP:
                    explicit_heap += amount
                else:
                    raise ValueError(
                        "bad kind for an explicit/ report: {}, {}".format(
                            path, str(kind)
                        )
                    )

                if path.startswith("explicit/images/"):
                    all_metrics["images"] += amount
                elif "top(none)/detached" in path:
                    all_metrics["top-none-detached"] += amount
                elif path.startswith("explicit/heap-overhead/"):
                    all_metrics["heap-overhead"] += amount

            elif path.startswith("js-main-runtime/"):
                all_metrics["js-main-runtime"] += amount

            elif path in metrics_measured:
                all_metrics[path] += amount

        if not pid_found:
            raise ValueError(f"no measurements found for pid {pid}")

        # Nb: sometimes heap-unclassified is negative due to bogus measurements
        # of some kind. We just show the negative value anyway.
        all_metrics["heap-unclassified"] = all_metrics["heap-allocated"] - explicit_heap
        all_metrics["explicit"] = all_metrics["heap-allocated"] + explicit_nonheap

        # Replace all dashes in keys with underscores to fit our crash
        # documents' naming conventions.
        memory_measures = {
            key.replace("-", "_"): val for key, val in all_metrics.items()
        }

        return memory_measures
