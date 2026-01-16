<script>
const TimeDrawer = defineAsyncComponent(() => import("@components/PlotlyTimeDrawer.vue"));
const LogDrawer = defineAsyncComponent(() => import("@components/PlotlyLogDrawer.vue"));

const CurrentDrawer = computed(() => {
  if (view.value === "time") return TimeDrawer;
  if (view.value === "log") return LogDrawer;
  return null;
});
</script>
