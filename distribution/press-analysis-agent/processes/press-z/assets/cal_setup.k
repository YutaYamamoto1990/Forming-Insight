$# LS-DYNA Keyword file created by LS-PrePost(R) V4.8.29 - 05Apr2022
$# Created on Sep-25-2026 (11:09:03)
*KEYWORD
*TITLE
$#                                                                         title
Hemispherical Deep Draw
*DATABASE_GLSTAT
$#      dt    binary      lcur     ioopt     
     0.005         0         0         1
*DATABASE_MATSUM
$#      dt    binary      lcur     ioopt     
     0.005         0         0         1
*DATABASE_NODOUT
$#      dt    binary      lcur     ioopt   option1   option2       
     0.005         0         0         1       0.0         0
*DATABASE_RBDOUT
$#      dt    binary      lcur     ioopt     
     0.005         0         0         1
*DATABASE_RCFORC
$#      dt    binary      lcur     ioopt     
     0.005         0         0         1
*DATABASE_BINARY_D3PLOT
$        f         i
$  dt/cycl      lcdt
$#      dt      lcdt      beam     npltc    psetid      
     0.005         0         0         0         0
$#   ioopt      rate    cutoff    window      type      pset    
         0       0.0       0.0       0.0         0         0
*DATABASE_BINARY_D3THDT
$        f         i
$  dt/cycl      lcdt
$#      dt      lcdt      beam     npltc    psetid      
      12.0         0         0         0         0
*DATABASE_EXTENT_BINARY
$        i         i         i         i         i         i         i         i
$    neiph     neips    maxint    strflg    sigflg    epsflg    rltflg    engflg
$#   neiph     neips    maxint    strflg    sigflg    epsflg    rltflg    engflg
         0         0         3         1         1         1         1         1
$        i         i         i
$   cmpflg    ieverp    beamip
$#  cmpflg    ieverp    beamip     dcomp      shge     stssz    n3thdt   ialemat
         0         0         0         1         1         1         2         1
*DATABASE_HISTORY_NODE
$        i         i         i         i         i         i         i         i
$      id1       id2       id3       id4       id5       id6       id7       id8
$#     id1       id2       id3       id4       id5       id6       id7       id8
         1       101         0         0         0         0         0         0
*CONTROL_CONTACT
$        f         f         i         i         i         i         i
$   slsfac    rwpnal    islchk    shlthk    penopt    thkchg     orien
$#  slsfac    rwpnal    islchk    shlthk    penopt    thkchg     orien    enmass
       0.1       1.0         1         1         1         0         1         0
$        i         i         i         i         f
$   usrstr    usrfac     nsbcs    interm    xpenen
$#  usrstr    usrfrc     nsbcs    interm     xpene     ssthk      ecdt   tiedprj
         0         0         0         0       4.0         0         0         0
$#   sfric     dfric       edc       vfc        th     th_sf    pen_sf      
       0.0       0.0       0.0       0.0       0.0       0.0       0.0
$#  ignore    frceng   skiprwg    outseg   spotstp   spotdel   spothin       
         0         0         0         0         0         0       0.0
$#    isym    nserod    rwgaps    rwgdth     rwksf      icov    swradf    ithoff
         0         0         1       0.0       1.0         0       0.0         0
$#  shledg    pstiff    ithcnt    tdcnof     ftall    unused    shltrw    igactc
         0         0         0         0         0                 0.0         0
*CONTROL_ENERGY
$        i         i         i         i
$     hgen      rwen    slnten     rylen
$#    hgen      rwen    slnten     rylen     irgen     
         2         2         2         1         2
*CONTROL_OUTPUT
$        i         i         i         i         f         i         i
$    npopt    neecho    nrefup    iaccop     opifs    ipnint    ikedit
$#   npopt    neecho    nrefup    iaccop     opifs    ipnint    ikedit    iflush
         0         0         0         0       0.0         0      1000      5000
$#   iprtf    ierode   tet10s8    msgmax    ipcurv      gmdt   ip1dblt      eocs
         0         0         2        50         0       0.0         0         0
$#   tolev    newleg    frfreq     minfo    solsig    msgflg    cdetol      
         2         0         1         0         0         0      10.0
$# phschng    demden   icrfile   spc2bnd    penout    shlsig   hisnout    engout
         0         0         0         0         0         0         0         0
$#    insf    isolsf      ibsf      issf    mlkbag      
         0         0         0         0         0
*CONTROL_SHELL
$        f         i         i         i         i         i         i
$   wrpang    itrist     irnxx    istupd    theory       bwc     miter
$#  wrpang     esort     irnxx    istupd    theory       bwc     miter      proj
      20.0         0        -1         1         2         2         1         0
$# rotascl    intgrd    lamsht    cstyp6    thshel      
       1.0         0         0         1         0
$# psstupd   sidt4tu     cntco    itsflg    irquad    w-mode   stretch      icrq
         0         0         0         0         2       0.0       0.0         0
*CONTROL_TERMINATION
$        f         i         f         f         f
$   endtim    endcyc     dtmin    endneg    endmas
$#  endtim    endcyc     dtmin    endeng    endmas     nosol     
       0.1         0       0.0       0.01.000000E8         0
*MAT_RIGID
$        f         f         f         f         f         f         f         f
$      mid        ro         e        pr         n    couple         m     alias
$#     mid        ro         e        pr         n    couple         m     alias
         27.83000E-9  207000.0       0.3       0.0       0.0       0.0          
$#     cmo      con1      con2    
       1.0         4         7
$#lco or a1        a2        a3        v1        v2        v3  
       0.0       0.0       0.0       0.0       0.0       0.0
*PART
$ c
$ head
$#                                                                         title
Rigid - Punch
$        i         i         i         i         i         i
$      pid       sid       mid     eosid      hgid    adpopt
$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid
         2         2         2         0         0         0         0         0
*SECTION_SHELL
$        i         i         f         f         f         f         i
$      sid    elform      shrf       nip     propt   qr/irid     icomp
$#   secid    elform      shrf       nip     propt   qr/irid     icomp     setyp
         2         2       1.0         5       1.0         0         0         1
$#      t1        t2        t3        t4      nloc     marea      idof    edgset
       1.0       1.0       1.0       1.0       0.0       0.0       0.0         0
*PART
$ c
$ head
$#                                                                         title
Rigid - Punch
$        i         i         i         i         i         i
$      pid       sid       mid     eosid      hgid    adpopt
$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid
         3         2         2         0         0         0         0         0
*PART
$ c
$ head
$#                                                                         title
Rigid - Punch
$        i         i         i         i         i         i
$      pid       sid       mid     eosid      hgid    adpopt
$#     pid     secid       mid     eosid      hgid      grav    adpopt      tmid
         4         2         2         0         0         0         0         0
*DEFINE_CURVE_TITLE
Osae
$        i         i         f         f         f         f
$     lcid      sidr      scla      sclo      offa      offo
$#    lcid      sidr       sfa       sfo      offa      offo    dattyp     lcint
         1         0       0.0       0.0       0.0       0.0         0         0
$#                a1                  o1  
                 0.0                 0.0
                0.01           -220000.0
                 0.1           -220000.0
*DEFINE_CURVE_TITLE
Zero
$        i         i         f         f         f         f
$     lcid      sidr      scla      sclo      offa      offo
$#    lcid      sidr       sfa       sfo      offa      offo    dattyp     lcint
         3         0       0.0       0.0       0.0       0.0         0         0
$#                a1                  o1  
                 0.0                 0.0
                 1.0                 0.0
*BOUNDARY_PRESCRIBED_MOTION_RIGID
$        i         i         i         i         f         i
$      pid       dof       vad      lcid        sf       vid
$#     pid       dof       vad      lcid        sf       vid     death     birth
         2         3         2         2      -1.0         01.00000E28       0.0
$        i         i         i         i         f         i
$      pid       dof       vad      lcid        sf       vid
$#     pid       dof       vad      lcid        sf       vid     death     birth
         4         3         2         3      -1.0         01.00000E28       0.0
*CONTACT_FORMING_ONE_WAY_SURFACE_TO_SURFACE
$#     cid                                                                 title
$        i         i         i         i         i         i         i         i
$     ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
         1         2         3         3         0         0         0         0
$        f         f         f         f         f         i         f         f
$       fs        fd        dc        vc       vdc    penchk        bt        dt
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
      0.15      0.15       0.0       0.0       0.0         0       0.01.00000E20
$        f         f         f         f         f         f         f         f
$      sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
*CONTACT_FORMING_ONE_WAY_SURFACE_TO_SURFACE
$#     cid                                                                 title
$        i         i         i         i         i         i         i         i
$     ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
         1         3         3         3         0         0         0         0
$        f         f         f         f         f         i         f         f
$       fs        fd        dc        vc       vdc    penchk        bt        dt
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
      0.15      0.15       0.0       0.0       0.0         0       0.01.00000E20
$        f         f         f         f         f         f         f         f
$      sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
*CONTACT_FORMING_ONE_WAY_SURFACE_TO_SURFACE
$#     cid                                                                 title
$        i         i         i         i         i         i         i         i
$     ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr
         1         4         3         3         0         0         0         0
$        f         f         f         f         f         i         f         f
$       fs        fd        dc        vc       vdc    penchk        bt        dt
$#      fs        fd        dc        vc       vdc    penchk        bt        dt
      0.15      0.15       0.0       0.0       0.0         0       0.01.00000E20
$        f         f         f         f         f         f         f         f
$      sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
$#     sfs       sfm       sst       mst      sfst      sfmt       fsf       vsf
       1.0       1.0       0.0       0.0       1.0       1.0       1.0       1.0
*LOAD_BODY_Z
$#    lcid        sf    lciddr        xc        yc        zc       cid   
         1       1.0         0       0.0       0.0       0.0         0
*LOAD_RIGID_BODY
$#     pid       dof      lcid        sf       cid        m1        m2        m3
         3         3         1       1.0         0         0         0         0
*SET_NODE_LIST
$        i         f         f         f         f
$      sid       da1       da2       da3       da4
$#     sid       da1       da2       da3       da4    solver      
         1       0.0       0.0       0.0       0.0MECH
$        i         i         i         i         i         i         i         i
$     nid1      nid2      nid3      nid4      nid5      nid6      nid7      nid8
$#    nid1      nid2      nid3      nid4      nid5      nid6      nid7      nid8
       900       901       902       903       904       905       906       907
       908       909       910       911       912       913       914       915
       916       917       918       919       920       921       922       923
       924       925       926       927       928       929       930       931
       932       933       934       935       936       937       938       939
       940       941       942       943       944       945       946       947
       948       949       950       951       952       953       954       955
       956       957       958       959       960       961       962       963
       964       965       966       967       968       969       970       971
       972       973       974       975       976       977       978       979
       980       981       982       983       984       985       986       987
       988       989       990       991       992       993       994       995
       996       997       998       999      1000      1001      1002      1003
      1004      1005      1006      1007      1008      1009      1010      1011
      1012      1013      1014      1015      1016      1017      1018      1019
      1020      1021      1022      1023      1024      1025      1026      1027
      1028      1029      1030      1031      1032      1033      1034      1035
      1036      1037      1038      1039      1040      1041      1042      1043
      1044      1045      1046      1047      1048      1049      1050      1051
      1052      1053      1054      1055      1056      1057      1058      1059
      1060      1061      1062      1063      1064      1065      1066      1067
      1068      1069      1070      1071      1072      1073      1074         0
*END
