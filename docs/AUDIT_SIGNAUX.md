# Audit du graphe de signaux

Analyse statique conservative des scripts effectivement reliés, y compris leurs modules inclus. Un écart reste un candidat à vérifier : certains objets du moteur peuvent traiter un signal sans gestionnaire de script littéral.

- 68 missions ou variantes ;
- 4894 scripts atteignables ;
- 5711 envois résolus vers un acteur ;
- 152 écarts à examiner.

| Mission | Émetteur | Cible | Signal | Script cible | Signaux gérés | Type |
|---|---|---|---:|---|---|---|
| africa1 | af1_08.scr | af1_07 | 10 | af1_07.scr | 1, 20 | sent_signal_not_handled |
| africa1 | af1_09.scr | af1_07 | 10 | af1_07.scr | 1, 20 | sent_signal_not_handled |
| africa1 | af1_10.scr | af1_07 | 10 | af1_07.scr | 1, 20 | sent_signal_not_handled |
| africa1 | af1_07.scr | af1_08 | 10 | af1_08.scr | 1, 20 | sent_signal_not_handled |
| africa1 | af1_09.scr | af1_08 | 10 | af1_08.scr | 1, 20 | sent_signal_not_handled |
| africa1 | af1_10.scr | af1_08 | 10 | af1_08.scr | 1, 20 | sent_signal_not_handled |
| africa1 | af1_07.scr | af1_09 | 10 | af1_09.scr | 1, 20 | sent_signal_not_handled |
| africa1 | af1_08.scr | af1_09 | 10 | af1_09.scr | 1, 20 | sent_signal_not_handled |
| africa1 | af1_10.scr | af1_09 | 10 | af1_09.scr | 1, 20 | sent_signal_not_handled |
| africa1 | af1_10.scr | af1_12 | 10 | af1_12.scr | 5, 20 | sent_signal_not_handled |
| africa1 | af1_inrange.scr | af1_23 | 10 | af1_23.scr | — | target_has_no_literal_signal_handler |
| africa1 | af1_21.scr | dummy_dabing_01 | 1 | af1_dabing_01.scr | — | target_has_no_literal_signal_handler |
| africa2 | af2_activator.scr | af2_02 | 5 | af2_02.scr | 1, 20 | sent_signal_not_handled |
| africa2 | af2_01.scr | af2_05 | 2 | af2_05.scr | 1, 5 | sent_signal_not_handled |
| africa2 | af2_hidejunkers.scr | af2_05 | 2 | af2_05.scr | 1, 5 | sent_signal_not_handled |
| africa2 | af2_dummy_alert01.scr | af2_05 | 20 | af2_05.scr | 1, 5 | sent_signal_not_handled |
| africa2 | af2_01.scr | af2_06 | 2 | af2_06.scr | 1, 5, 20 | sent_signal_not_handled |
| africa2 | af2_hidejunkers.scr | af2_06 | 2 | af2_06.scr | 1, 5, 20 | sent_signal_not_handled |
| africa2 | af2_13.scr | af2_activator | 1 | af2_activator.scr | 5 | sent_signal_not_handled |
| africa3 | af3a_rozhovor_05.scr | af3a_02 | 10 | af3a_02.scr | 20 | sent_signal_not_handled |
| africa3 | af3a_rozhovor_05.scr | af3a_02 | 11 | af3a_02.scr | 20 | sent_signal_not_handled |
| africa3 | af3a_rozhovor_05.scr | af3a_03 | 11 | af3a_03.scr | 10, 20 | sent_signal_not_handled |
| africa3 | af3a_rozhovor_04.scr | af3a_05 | 10 | af3a_05.scr | 1, 2, 20 | sent_signal_not_handled |
| africa3 | af3a_rozhovor_04.scr | af3a_05 | 11 | af3a_05.scr | 1, 2, 20 | sent_signal_not_handled |
| africa3 | af3a_rozhovor_04.scr | af3a_06 | 10 | af3a_06.scr | 1, 2, 20 | sent_signal_not_handled |
| africa3 | af3a_rozhovor_04.scr | af3a_06 | 11 | af3a_06.scr | 1, 2, 20 | sent_signal_not_handled |
| africa3 | af3a_16_activator.scr | af3a_16 | 1 | af3a_16.scr | — | target_has_no_literal_signal_handler |
| africa3 | af3a_doctor_activator.scr | af3a_19 | 16 | af3a_19.scr | — | target_has_no_literal_signal_handler |
| africa3 | af3a_25_detector.scr | af3a_25 | 10 | af3a_25.scr | — | target_has_no_literal_signal_handler |
| africa3 | af3a_rozhovor_03.scr | af3a_28 | 10 | af3a_28.scr | — | target_has_no_literal_signal_handler |
| africa3 | af3a_rozhovor_03.scr | af3a_28 | 11 | af3a_28.scr | — | target_has_no_literal_signal_handler |
| africa3 | af3a_rozhovor_03.scr | af3a_29 | 10 | af3a_29.scr | — | target_has_no_literal_signal_handler |
| africa3 | af3a_rozhovor_03.scr | af3a_29 | 11 | af3a_29.scr | — | target_has_no_literal_signal_handler |
| africa3 | af3a_doctor_activator.scr | af3a_doktor | 16 | af3a_doktor.scr | — | target_has_no_literal_signal_handler |
| africa3 | af3a_doktor_detector.scr | af3a_doktor | 16 | af3a_doktor.scr | — | target_has_no_literal_signal_handler |
| africa3 | af3a_doktor_detector.scr | af3a_pacient02 | 16 | af3a_pacient02.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_01.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_02.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_03.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_04.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_05.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_06.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_07.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_08.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_09.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_10.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_11.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_12.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_13.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_14.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_15.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_16.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_17.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_18.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_19.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_20.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_21.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_22.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_23.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_24.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_25.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_26.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_27.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_28.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_29.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_30.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_31.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_32.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_33.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_tankista02.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_tankista03.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_tankista05.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4 | af3b_tankista06.scr | dummy_organizer | 1 | af3b_organizer.scr | — | target_has_no_literal_signal_handler |
| africa4_obj | af4_mp_barikada.scr | m_palma3 | 1 | af4_mp_barikada.scr | — | target_has_no_literal_signal_handler |
| africa5 | af4_44.scr | af4_43 | 5 | af4_43.scr | — | target_has_no_literal_signal_handler |
| africa5 | af4_49.scr | af4_43 | 5 | af4_43.scr | — | target_has_no_literal_signal_handler |
| africa5 | af4_sklad_activator.scr | af4_sklad04 | 1 | af4_sklad04.scr | — | target_has_no_literal_signal_handler |
| alps1 | ge_34.scr | ge_33 | 3 | ge_33.scr | 1 | sent_signal_not_handled |
| alps1 | signal_k_ohni.scr | ge_33 | 3 | ge_33.scr | 1 | sent_signal_not_handled |
| alps1 | signal_k_ohni.scr | ge_35 | 3 | ge_35.scr | 1 | sent_signal_not_handled |
| alps1 | signal_ke_strelnici.scr | ge_35 | 3 | ge_35.scr | 1 | sent_signal_not_handled |
| alps1 | ge_36.scr | ge_35 | 4 | ge_35.scr | 1 | sent_signal_not_handled |
| alps2 | al2_01_a1.scr | al2_01 | 1 | al2_01.scr | 4, 6, 8 | sent_signal_not_handled |
| alps2 | al2_alarm_carn.scr | al2_35 | 2 | al2_35.scr | 1 | sent_signal_not_handled |
| alps2 | al2_01.scr | al2_alarm | 1 | al2_alarm.scr, al2_alarm_carn.scr | 5, 6 | sent_signal_not_handled |
| arctic2 | r_arc1b_w1.scr | dummy_globalalarm | 3 | r_arc1b_globalalarm.scr | 1, 2 | sent_signal_not_handled |
| arctic2 | r_arc1b_w2.scr | dummy_globalalarm | 3 | r_arc1b_globalalarm.scr | 1, 2 | sent_signal_not_handled |
| arctic2 | r_arc1b_w3.scr | dummy_globalalarm | 3 | r_arc1b_globalalarm.scr | 1, 2 | sent_signal_not_handled |
| arctic2 | r_arc1b_w4.scr | dummy_globalalarm | 3 | r_arc1b_globalalarm.scr | 1, 2 | sent_signal_not_handled |
| arctic2 | r_arc1b_w5.scr | dummy_globalalarm | 3 | r_arc1b_globalalarm.scr | 1, 2 | sent_signal_not_handled |
| arctic2 | r_arc1b_w6.scr | dummy_globalalarm | 3 | r_arc1b_globalalarm.scr | 1, 2 | sent_signal_not_handled |
| arctic2 | r_arc1b_w7.scr | dummy_globalalarm | 3 | r_arc1b_globalalarm.scr | 1, 2 | sent_signal_not_handled |
| brest | mesh24.scr | z2_agresor1 | 1 | z2_agresor1.scr | — | target_has_no_literal_signal_handler |
| burgundy1 | bur1_04.scr | bu1_driver01 | 1 | bur1_driver01.scr | — | target_has_no_literal_signal_handler |
| burgundy1 | bur1_04.scr | la_zavora_.zavora | 0 | zavora.scr | 1, 2 | sent_signal_not_handled |
| burgundy2 | ge_motorka.scr | ge_dilna | 3 | ge_dilna.scr | 1, 2 | sent_signal_not_handled |
| burgundy3 | bur3_rozhovor.scr | bur03_20 | 11 | bur3_20.scr | — | target_has_no_literal_signal_handler |
| burgundy3 | bur3_rozhovor.scr | bur03_20 | 13 | bur3_20.scr | — | target_has_no_literal_signal_handler |
| burgundy3 | bur3_rozhovor.scr | bur03_20 | 15 | bur3_20.scr | — | target_has_no_literal_signal_handler |
| burgundy3 | bur3_rozhovor.scr | bur03_20 | 17 | bur3_20.scr | — | target_has_no_literal_signal_handler |
| burgundy3 | bur3_rozhovor.scr | bur03_sas02 | 10 | bur3_sas02.scr | — | target_has_no_literal_signal_handler |
| burgundy3 | bur3_rozhovor.scr | bur03_sas02 | 12 | bur3_sas02.scr | — | target_has_no_literal_signal_handler |
| burgundy3 | bur3_rozhovor.scr | bur03_sas02 | 14 | bur3_sas02.scr | — | target_has_no_literal_signal_handler |
| burgundy3 | bur3_rozhovor.scr | bur03_sas02 | 16 | bur3_sas02.scr | — | target_has_no_literal_signal_handler |
| burgundy3 | bur3_maquis01.scr | e_treeb_160 | 10 | snd_vybuch_paliva.scr | — | target_has_no_literal_signal_handler |
| burgundy3 | bur3_vybuch.scr | e_treeb_160 | 10 | snd_vybuch_paliva.scr | — | target_has_no_literal_signal_handler |
| co_brest | mesh24.scr | z2_agresor1 | 1 | z2_agresor1.scr | — | target_has_no_literal_signal_handler |
| co_burgundy1 | bur1_04.scr | bu1_driver01 | 1 | bur1_driver01.scr | — | target_has_no_literal_signal_handler |
| co_burgundy1 | bur1_04.scr | la_zavora_.zavora | 0 | zavora.scr | 1, 2 | sent_signal_not_handled |
| co_burgundy2 | detect_motopryc.scr | objectyves | 3 | objectyves.scr | 1, 2 | sent_signal_not_handled |
| co_burgundy2 | detect_motopryc.scr | objectyves | 4 | objectyves.scr | 1, 2 | sent_signal_not_handled |
| co_burgundy3 | bur3_rozhovor.scr | bur03_20 | 11 | bur3_20.scr | — | target_has_no_literal_signal_handler |
| co_burgundy3 | bur3_rozhovor.scr | bur03_20 | 13 | bur3_20.scr | — | target_has_no_literal_signal_handler |
| co_burgundy3 | bur3_rozhovor.scr | bur03_20 | 15 | bur3_20.scr | — | target_has_no_literal_signal_handler |
| co_burgundy3 | bur3_rozhovor.scr | bur03_20 | 17 | bur3_20.scr | — | target_has_no_literal_signal_handler |
| co_burgundy3 | bur3_rozhovor.scr | bur03_sas02 | 10 | bur3_sas02.scr | — | target_has_no_literal_signal_handler |
| co_burgundy3 | bur3_rozhovor.scr | bur03_sas02 | 12 | bur3_sas02.scr | — | target_has_no_literal_signal_handler |
| co_burgundy3 | bur3_rozhovor.scr | bur03_sas02 | 14 | bur3_sas02.scr | — | target_has_no_literal_signal_handler |
| co_burgundy3 | bur3_rozhovor.scr | bur03_sas02 | 16 | bur3_sas02.scr | — | target_has_no_literal_signal_handler |
| co_libye1 | af1_48_af1_49_speech.scr | af1_48 | 2 | af1_48.scr | 1 | sent_signal_not_handled |
| co_libye1 | af1_48_af1_49_speech.scr | af1_49 | 2 | af1_49.scr | 1 | sent_signal_not_handled |
| co_libye1 | af1_obj2_succ_sender.scr | objectives | 3 | af1_objectives.scr | 1, 6 | sent_signal_not_handled |
| co_libye2 | af2_obj3.scr | af2_obj | 2 | af2_objective.scr | 1 | sent_signal_not_handled |
| czech2 | r_cz2_ger21.scr | big_boss | 1 | r_cz2_big_boss.scr | 19 | sent_signal_not_handled |
| czech2 | freiberg_attack01.scr | big_boss | 3 | r_cz2_big_boss.scr | 19 | sent_signal_not_handled |
| czech2 | freiberg_attack02.scr | big_boss | 4 | r_cz2_big_boss.scr | 19 | sent_signal_not_handled |
| czech2 | r_cz2_ger16.scr | ger_20 | 1 | r_cz2_ger20.scr | — | target_has_no_literal_signal_handler |
| czech2 | r_cz2_ger22.scr | ger_24 | 2 | r_cz2_ger24.scr | 3 | sent_signal_not_handled |
| czech2 | r_cz2_ger23.scr | ger_24 | 2 | r_cz2_ger24.scr | 3 | sent_signal_not_handled |
| czech2 | r_cz2_ger22.scr | ger_25 | 2 | r_cz2_ger25.scr | 3 | sent_signal_not_handled |
| czech2 | r_cz2_ger23.scr | ger_25 | 2 | r_cz2_ger25.scr | 3 | sent_signal_not_handled |
| czech2 | endgame.scr | objectives | 2 | objectives_carn.scr, r_cz2_objectives.scr | 1, 3, 4, 5, 6, 19 | sent_signal_not_handled |
| czech3 | r_cz3_dummy_alarm.scr | commander | 2 | r_cz3_commander.scr | — | target_has_no_literal_signal_handler |
| czech3 | ci1.scr | e_ktable3 | 2 | setobjectives.scr | — | target_has_no_literal_signal_handler |
| czech3 | ci2.scr | e_ktable3 | 2 | setobjectives.scr | — | target_has_no_literal_signal_handler |
| czech4 | cz4_apumperz_01.scr | cz4_platoon_04 | 5 | cz4_platoon_04.scr | — | target_has_no_literal_signal_handler |
| czech4 | cz4_detector_04.scr | cz4_plazzars_02 | 4 | cz4_plazzars_02.scr | 3, 7, 16 | sent_signal_not_handled |
| czech4 | cz4_detector_04.scr | cz4_plazzars_03 | 4 | cz4_plazzars_03.scr | 3, 7, 16 | sent_signal_not_handled |
| czech4 | cz4_detector_01.scr | cz4_sniper_01 | 1 | cz4_sniper_01.scr | — | target_has_no_literal_signal_handler |
| czech6 | c5_g40.scr | c5_g11 | 1 | c5_g11.scr | 2 | sent_signal_not_handled |
| czech6 | c5_g40.scr | c5_g43 | 1 | c5_g43.scr | — | target_has_no_literal_signal_handler |
| libye1 | af1_48_af1_49_speech.scr | af1_48 | 2 | af1_48.scr | 1 | sent_signal_not_handled |
| libye1 | af1_48_af1_49_speech.scr | af1_49 | 2 | af1_49.scr | 1 | sent_signal_not_handled |
| libye2 | af2_obj3.scr | af2_obj | 2 | af2_objective.scr, af2_objective2.scr | 1 | sent_signal_not_handled |
| libye3 | li3_cargo.scr | li3_german_con_2 | 1 | li3_german_con_2.scr | — | target_has_no_literal_signal_handler |
| normandy2 | r_n2_detector_7.scr | red_26 | 7 | r_n2_red_26.scr | 6 | sent_signal_not_handled |
| norway | detect_player1.scr | detect_player1 | 2 | detect_player1.scr | 1 | sent_signal_not_handled |
| tutorial | tut_dummy_pike1in.scr | controlortwo | 1 | tut_piker_1.scr | — | target_has_no_literal_signal_handler |
| tutorial | tut_dummy_pike1in.scr | controlortwo | 2 | tut_piker_1.scr | — | target_has_no_literal_signal_handler |
| tutorial | tut_instructor1_aid.scr | dummy_ba_counter | 17 | tut_dummy_ba_counter.scr | 1, 2, 3, 4, 5 | sent_signal_not_handled |
| tutorial | tut_tmode_controller.scr | dummy_wi | 1 | tut_dummy_wi.scr | — | target_has_no_literal_signal_handler |
| tutorial | tut_instructor6.scr | t_dummy_hr_check | 1 | t_hr_check.scr | — | target_has_no_literal_signal_handler |
