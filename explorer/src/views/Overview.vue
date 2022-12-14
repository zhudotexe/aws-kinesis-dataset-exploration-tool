<script setup lang="ts">
import type {DatasetClient} from "@/client";
import DatasetTable from "@/components/DatasetTable.vue";
import {ref} from "vue";
import {useRouter} from "vue-router";

const props = defineProps<{ client: DatasetClient }>();
const router = useRouter();

// data
const viewInstanceId = ref("");
const viewInstanceIdError = ref("");

// methods
function onViewInstanceId() {
  if (!props.client.instanceIds.includes(viewInstanceId.value)) {
    viewInstanceIdError.value = "This instance is not in the dataset.";
    return;
  }
  router.push(`/instances/${viewInstanceId.value}`);
}

async function onViewRandom() {
  const randomInstanceId = props.client.instanceIds[Math.floor(Math.random() * props.client.instanceIds.length)];
  const routeData = router.resolve(`/instances/${randomInstanceId}`);
  await navigator.clipboard.writeText(randomInstanceId);
  window.open(routeData.href, '_blank');
}
</script>

<template>
  <div>
    <section class="section">
      <h1 class="title">Dataset Overview</h1>
      <p v-if="!client.indexLoaded">
        Loading...
      </p>
      <div v-else>
        <p>
          Welcome to AWS Kinesis Dataset Exploration Tool. {{ client.instanceIds.length }} instances loaded for dataset
          {{ client.checksum }}.
        </p>
        <p>
          Select an instance below to view its events, or enter an instance ID here to view it:
        </p>
        <div class="field has-addons">
          <div class="control is-expanded">
            <input class="input" type="text" placeholder="Instance ID" v-model="viewInstanceId">
            <p class="help is-danger" v-if="viewInstanceIdError">{{ viewInstanceIdError }}</p>
          </div>
          <div class="control">
            <a class="button is-info" @click="onViewInstanceId()">
              Go
            </a>
          </div>
        </div>
        <div>
          <button class="button is-info" @click="onViewRandom()">
            Open Random in new tab
          </button>
          <a class="button is-info" :href="client.apiBase + '/heuristics/csv'" target="_blank">
            Export to CSV
          </a>
        </div>
      </div>
    </section>

    <section class="section" v-if="client.heuristicsLoaded">
      <DatasetTable :client="client"/>
    </section>
  </div>
</template>
